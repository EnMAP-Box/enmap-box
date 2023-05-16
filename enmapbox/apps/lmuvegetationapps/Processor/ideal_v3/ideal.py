# -*- coding: utf-8 -*-
"""
IDEAL - Inverse-Distance based Exploration for Active Learning

An active learning algorithm for regression and classification (pool-based version)
described in the following paper:

[1] A. Bemporad, “Active learning for regression by inverse distance weighting,”
 2022, Submitted for publication. Available on http://arxiv.org/abs/2204.07177.

The following methods are also implemented for comparison:

- RANDOM:    queries are performed randomly
- GREEDY_x:  queries are performed by selecting the sample with maximum min-distance
             from the samples already selected. This is GSx method in (Wu, Lin, Huang, 2019),
             Algorithm 1 (pool-based sampling only)
- GREEDY_xy: iGS method in (Wu, Lin, Huang, 2019), Algorithm 3
- QBC:       query-by-committee (Burbridge, Rowland, King, 2007), based on N_qbc predictors
- iRDM:      improved representativeness-diversity maximization (Liu, Jiang, Luo, Fang, Liu, Wu, 2021)

(C) 2022 A. Bemporad, April 14, 2022
    Revised by A. Bemporad, October 20, 2022
    Revised by A. Bemporad, December 9, 2022
"""

import numpy as np
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.base import clone
from sklearn.cluster import KMeans
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import NearestNeighbors
from numba import jit  # required to speedup method 'iRDM'


##############################################################################
# Functions
##############################################################################

# function used in iRDM method in ideal_training
@jit(nopython=True)
def set_update(M, I0, Xs, R, nC, iClist):
    D = np.zeros(R.shape[0])
    n = Xs.shape[1]
    for m in range(M):
        nCm = nC[m]
        iC = iClist[0:nCm, m]  # indices of points in cluster #label
        for i in range(nC[m]):
            dist = np.sqrt(np.sum((Xs[iC[i]] - Xs[I0]) ** 2, axis=1))
            dist[m] = np.inf
            D[iC[i]] = np.min(dist)
        nstar = np.argmax(D[iC] - R[iC])
        I0[m] = iC[nstar]
    return I0


##############################################################################

def ideal_training(data, pred, pred_type, n_init, maxevals, train_interval=1,
                   delta=5.0, use_gradient=0, method='ideal', N_qbc=5, qbc_method='bootstrap',
                   N_iRDM=5, init_method=None,
                   verbose=1, loss=None, unknown_constraint=False, known_constraint_fcn=None,
                   density_weight=0.0):
    """
    IDEAL - Inverse-Distance based Exploration for Active Learning
    An active learning algorithm for regression and classification (pool-based version).
    
    (C) 2022 A. Bemporad, April 14, 2022

    Samples are incrementally selected from a training dataset X and the corresponding
    target sample is extracted from Y. The function must return Y[i]=Inf or Y[i]=NaN
    in case the target cannot be acquired, so to model unknown constraints on x.

    For making comparisons, the method also supports passive methods of random sampling,
    greedy sampling based on distances between feature vectors (Yu, Kim, 2010),
    and the improved representativeness-diversity maximization method
    (Liu, Jiang, Luo, Fang, Liu, Wu, 2021).

    For regression problems only, the method also supports greedy sampling based on feature
    vectors and predicted targets (Wu, Lin, Huang, 2019), and query-by-committee
    for regression (Burbidge, Rowland, King, 2007) based on bootstrap subsets
    (with repetitions).

    The fitting score of each predictor is computed on all training and, if provided,
    test samples to evaluate the performance of the active learning method.

    :param data:
        data["X"]:  pool of feature vectors in training dataset to extract from.
        data["Y"]:  either target values in training dataset corresponding to X or a generator function.
                    1) target values: an array of target values with as many entries as there are vectors in X
                    In case data["Y"] contains categorical values, these will be one-hot encoded.
                    Scoring results are computed on the entire feasible subset of the dataset (X,Y)
                    2) generator function: data["Y"] must return as many columns as there are targets and
                    as many rows as the number N of rows in X. The function must already return one-hot encoded values
                    in the case of categorical targets. Scoring results are only computed on the acquired samples.

        data["ny"]: target dimension, only consumed when data["Y"] is a generator function.
        data["X_test"]:  feature vectors in test dataset, only used to compute scores.
        data["Y_test"]:  targets in test dataset.

    :param pred: predictor (in scikit-learn format)

    :param pred_type: prediction type, either 'regression' (default) or 'classification'

    :param n_init: number of initial samples (queried according to init_method)

    :param maxevals: number of total samples that can be queried.
                     When method 'iRDM' is used, set maxevals=n_init to run active learning once,
                     otherwise active learning is run several times, each time acquiring M samples,
                     M=n_init,n_init+1,...,maxevals

    :param train_interval: re-train predictor every 'train_interval' queries (default: 1)

    :param delta: weight on IDW function for pure exploration (default: delta=0.0).
            If equal to 0.0, acquisition is purely based on IDW variance.

    :param method: active learning method used
        'ideal'
        'random'    queries are performed randomly
        'greedy_x'  queries are performed by selecting the sample with
                    maximum min-distance from the samples already selected
                    GSx method in (Wu, Lin, Huang, 2019), Algorithm 1
        'greedy_xy' iGS method in (Wu, Lin, Huang, 2019), Algorithm 3
        'qbc'       query-by-committee (Burbridge, Rowland, King, 2007), based on N_qbc predictors
        'iRDM'      improved representativeness-diversity maximization (Liu, Jiang, Luo, Fang, Liu, Wu, 2021)

    :param N_qbc: number of predictors used in QBC sampling

    :param qbc_method: QBC method used to create subsets of the current set of k acquired samples:
                'bootstrap': create bootstrap subsets of dimension k (with repetitions) from the existing samples
                'leave-out': leaves out floor(k/N_qbc) samples, where k=number of samples acquired.
                            This method may not perform well when k remains small.

    :param N_iRDM: max number of iRDM iterations used in iRDM sampling

    :param init_method: method used to generate initial n_init samples
        'kmeans' use K-means (only pool-based sampling)
        'greedy' use greedy method as in (Wu, Lin, Huang, 2019) (pool-based sampling only)
        'random' generate samples randomly
        'lhs'    use Latin Hypercube Sampling (query synthesis only)

    :param verbose: verbosity level (0=None)

    :param loss: function handle to a function g(x,yhat) used in acquisition to penalize
        g(x,yhat(x))(s(x)+delta*z(x)) instead of s(x)_delta*z(x) (default: g(x,yhat)=1 for all x,yhat).
        The function loss must accept vectorized inputs, i.e., loss(X,Y)[i]=loss(X[i],Y[i]).

    :param unknown_constraint: flag, set equal to True if Y may contain Inf or NaN's
                     due to unknown constraints, or in other words set the flag to False if
                     all x=X[i] are feasible and have a corresponding finite y(x)=Y[i]

    :param known_constraint_fcn: function handle of constraint function c(x)<=0, used to check
                     whether a selected point x can be queried (c_i(x)<=0 for all 1,...,nc) or not.
                     The function c(X) must return as many columns as there are constraints and
                     as many rows as the number N of rows in X. Default: no constraint.

    param: density_weight: used to weight the average distance from the n = dim(x) nearest neighbors
                        as a representativeness index during acquisition. When density_weight = 0,
                        no representativeness index is taken into account.

    :return:
        pred: final predictor after active learning
        samples: queried samples (X_act,Y_act), corresponding index (I_act), and their feasibility (Q_act)
        scores: scores on training and test datasets (if provided)

    """

    isloss = callable(loss)
    isKnownConstr = callable(known_constraint_fcn)
    isGreedy_x = (method.lower() == 'greedy_x')
    isGreedy_xy = (method.lower() == 'greedy_xy')
    if pred_type == 'classification' and isGreedy_xy:
        raise Exception('Greedy-XY method not applicable to classification problems.')
    isRandom = (method.lower() == 'random')
    isQBC = (method.lower() == 'qbc')
    if isQBC:
        isQBCbootstrap = (qbc_method.lower() == 'bootstrap')
        isQBCleaveout = (qbc_method.lower() == 'leave-out')
    if pred_type == 'classification' and isQBC:
        raise Exception('QBC method not implemented for classification problems, yet.')
    isIDEAL = (method.lower() == 'ideal')
    isiRDM = (method.lower() == 'irdm')

    if init_method is None:
        if isRandom or isQBC:
            init_method = 'random'
        elif isGreedy_x or isGreedy_xy:
            init_method = 'greedy'
        else:
            init_method = 'kmeans'

    if 'X_test' in data:
        X_test = np.array(data["X_test"])
        Y_test = np.array(data["Y_test"])
        if len(Y_test.shape) == 1:
            Y_test = Y_test.reshape(-1, 1)
    else:
        X_test = []
        Y_test = []
    isTest = len(X_test) > 0

    if (not 'X' in data) or (not 'Y' in data):
        error_msg = 'Please provide a pool of feature vectors and either the corresponding target values\n'
        error_msg = error_msg + 'or a generator function for the target.'
        raise Exception(error_msg)
    X = data["X"]
    Y = data["Y"]
    isGeneratorFcn = callable(Y)
    if isGeneratorFcn:
        generator_fcn = Y
    else:
        if len(Y.shape) < 2:
            Y = Y.reshape(-1, 1)

    # Get box of training feature vectors
    Xmin = np.min(X, axis=0)
    Xmax = np.max(X, axis=0)
    useDensity = (density_weight > 0.0)

    # remove possible duplicates
    Nx = X.shape[0]
    X, ii = np.unique(X, axis=0, return_index=True)
    if not isGeneratorFcn:
        Y = Y[ii]
    if Nx > X.shape[0]:
        print("Duplicate feature vectors found in pool and removed.")

    # Compute scaling factors for regressor, to have -1 <= (X-Xbias)/Xscale <= 1
    Xbias = (Xmax + Xmin) / 2.
    Xscale = (Xmax - Xmin) / 2.

    if pred_type == 'classification':
        if not isGeneratorFcn:
            Yenc = OneHotEncoder(handle_unknown='ignore', drop='if_binary').fit(Y.reshape(-1, 1))
            Y = Yenc.transform(Y.reshape(-1, 1)).toarray()
        check_warm_start = hasattr(pred, 'warm_start')
        if check_warm_start:
            pred_warm_start = pred.warm_start

    if not isGeneratorFcn:
        if len(Y.shape) == 1:
            Y = Y.reshape(-1, 1)
        ny = Y.shape[1]
    else:
        if (not 'ny' in data):
            error_msg = 'Please specify the dimension ny of the target vector.'
            raise Exception(error_msg)
        ny = data["ny"]

    if not isGeneratorFcn:
        isYfin = np.all(np.isfinite(Y), axis=1)
        Y_score = Y[isYfin]
        X_score = X[isYfin]

    if isTest:
        isYfin_test = np.all(np.isfinite(Y_test), axis=1)
        Y_test = Y_test[isYfin_test]
        X_test = X_test[isYfin_test]

    Xs = (X - Xbias) / Xscale
    N, nx = X.shape
    I_act = np.zeros(maxevals, dtype=int)
    used = np.zeros(N, dtype=bool)
    if useDensity:
        # possible duplicates were already removed
        K = nx + 1
        near_neigh = NearestNeighbors(n_neighbors=K).fit(X)  # xk itself is listed as a neighbor
        near_neigh_dist, _ = near_neigh.kneighbors(X)
        Dens = np.sum(near_neigh_dist, axis=1) / (K - 1)  # average Euclidean distance
        Dens = Dens ** nx  # average volume of a hyper-sphere (up to a constant).
        Dens = 1. / Dens  # density
        Dens = 1. + Dens / np.max(Dens) * density_weight

    X_act = np.zeros((maxevals, nx))
    Xs_act = np.zeros((maxevals, nx))
    Y_act = np.zeros((maxevals, ny))
    Q_act = np.zeros(maxevals, dtype=bool)

    if isIDEAL:
        W = np.zeros((N, maxevals))  # allocate IDW factors from queried samples for speed
        if delta > 0:
            SiD = np.zeros(N)
            Z = np.zeros(N)
            pi2 = 2. / np.pi
        Dmin = []
    else:
        Dmin = np.zeros(N)  # allocate min squared distances from queried samples for speed
        W, SW, Z = [[], [], []]

    if isKnownConstr:
        # only keep feasible points
        isfeas = np.all(known_constraint_fcn(X) <= 0, axis=1)
        used = used[isfeas]
        X = X[isfeas]
        Xs = Xs[isfeas]
        if not isGeneratorFcn:
            Y = Y[isfeas]
        N = X.shape[0]
        maxevals = min(maxevals, N)

    if init_method == 'random':
        random_indices = np.random.permutation(N)
        used_samples = 0
    else:
        Xs_copy = Xs.copy()

    if not isiRDM:
        # Extract first n_init feasible and queryable points
        n0 = 0
        init_evals = 0
        nfeas = 0
        while nfeas < n_init:
            nn = n_init - nfeas
            if n0 + nn > maxevals:
                raise Exception("Could not get %d initial samples after maxevals = %d queries. Increase maxevals." %
                                (n_init, maxevals))
            I0 = np.zeros(nn).astype(int)
            if init_method == 'kmeans':
                # Use K-means for both IDEAL and Greedy methods
                kmeans = KMeans(n_clusters=nn, init='k-means++', n_init=10).fit(Xs)
                if kmeans.n_clusters < nn:
                    raise Exception("Number of centroids too small, decrease n_init")
                for i in range(nn):
                    xsc = kmeans.cluster_centers_[i]
                    ind = np.argmin(np.sum((Xs_copy - xsc) ** 2, axis=1))
                    I0[i] = ind
                    used[ind] = True
                    Xs_copy[ind] = 1.e8  # to avoid the same xs is selected again
            elif init_method == 'random':
                I0 = random_indices[init_evals:init_evals + nn].astype(int)
                used[[i for i in I0]] = True
                used_samples += nn
            elif init_method == 'greedy':
                # Init method as in (Wu, Lin, Huang, 2019)
                xsc = np.sum(Xs, axis=0)  # centroid of pool
                ind = np.argmin(np.sum((Xs - xsc) ** 2, axis=1))  # Identify sample closest to xsc
                for i in range(nn):
                    I0[i] = ind
                    used[ind] = True
                    if i < nn - 1:
                        # find point with the largest minimum distance from the points already found
                        d = np.zeros(N)
                        for j in range(N):
                            if not used[j]:
                                d[j] = np.min(np.sum((Xs[used] - Xs[j]) ** 2,
                                                     axis=-1))  # min of squared distances from samples acquired so far
                        ind = np.argmax(d)

                X0 = X[I0]

            X0 = X[I0]
            if not isGeneratorFcn:
                Y0 = Y[I0]
            else:
                Y0 = generator_fcn(X0)

            init_evals += nn
            X_act[n0:n0 + nn] = X0
            Y_act[n0:n0 + nn] = Y0
            Q_act[n0:n0 + nn] = np.all(np.isfinite(Y0),
                                       axis=1)  # targets that could not be acquired were labeled as Inf or NaN

            I_act[n0:n0 + nn] = I0.reshape(-1)
            nfeas += np.sum(Q_act[n0:n0 + nn])
            n0 += nn

        Ymax = np.max(Y_act[0:init_evals][Q_act[0:init_evals]], axis=0)
        Ymin = np.min(Y_act[0:init_evals][Q_act[0:init_evals]], axis=0)
        ii = (Ymax - Ymin < 1.e-8)
        Ymax[ii] += 1.e-8  # This prevents 0/0 in case dY=0 and norm(dy)=0

        # Compute scaling factors for targets
        Yscale = (Ymax - Ymin) / 2.

        Xs_act[0:init_evals] = (X_act[0:init_evals] - Xbias) / Xscale

        Yhat = np.zeros((N, ny))

        if isIDEAL or isGreedy_x or isGreedy_xy:
            # Squared distances from samples acquired so far
            for i in range(init_evals):
                d = np.sum((Xs - Xs_act[i]) ** 2, axis=-1)
                if isIDEAL:
                    W[0:I_act[i], i] = np.exp(-d[0:I_act[i]]) / d[0:I_act[i]]
                    W[I_act[i] + 1:, i] = np.exp(-d[I_act[i] + 1:]) / d[I_act[i] + 1:]
                    if delta > 0:
                        SiD[0:I_act[i]] += 1. / d[0:I_act[i]]
                        SiD[I_act[i] + 1:] += 1. / d[I_act[i] + 1:]
                elif isGreedy_x or isGreedy_xy:
                    if i == 0:
                        Dmin = d
                    else:
                        Dmin = np.minimum(Dmin, d)  # component-wise minimum

        if isIDEAL:
            SW = np.sum(W[:, 0:init_evals], axis=1)
            if delta > 0:
                for i in range(init_evals):
                    Z[0:I_act[i]] = np.arctan(1. / SiD[0:I_act[i]]) * pi2
                    Z[I_act[i] + 1:] = np.arctan(1. / SiD[I_act[i] + 1:]) * pi2
    else:
        init_evals = n_init
        nx = X.shape[1]

    m = init_evals

    score_train = np.nan
    scores_train = np.nan * np.ones(maxevals)
    score_test = np.nan
    scores_test = np.nan * np.ones(maxevals)

    maxevals = min(maxevals, N)
    retrain = True
    if isQBC:
        preds = []
        for j in range(N_qbc):
            preds.append(clone(pred))
    thedelete = ""

    if unknown_constraint and not isiRDM:
        # Prepare predictor to possibly assign unqueriable data to predicted values
        if ny == 1:
            pred.fit(X_act[0:m][Q_act[0:m]], Y_act[0:m][Q_act[0:m]].reshape(-1))
        else:
            pred.fit(X_act[0:m][Q_act[0:m]], Y_act[0:m][Q_act[0:m]])

    while m <= maxevals:
        if m / train_interval == round(m / train_interval) or m == init_evals or m == maxevals:
            if verbose == 2:
                print("N = %3d/%3d: " % (m, maxevals), end="")

            if isiRDM:
                kmeans = KMeans(n_clusters=m, init='k-means++', n_init=10).fit(Xs)
                if kmeans.n_clusters < m:
                    raise Exception("Number of centroids too small, decrease n_init")
                I0 = np.zeros(m).astype(int)
                for i in range(m):
                    xsc = kmeans.cluster_centers_[i]
                    ind = np.argmin(np.sum((Xs - xsc) ** 2, axis=1))
                    I0[i] = ind

                # perform Algorithm 1 in (Liu, Jiang, Luo, Fang, Liu, Wu, 2021)
                P = np.zeros((N_iRDM, m), dtype=int)  # matrix used to store index combinations
                P[0] = np.sort(I0)
                nC = np.zeros(m, dtype=int)  # number of points in each cluster
                labels = kmeans.labels_
                iClist = np.zeros((N, m), dtype=int)
                for i in range(m):
                    iC = np.where(labels == i)[0]
                    nC[i] = iC.shape[0]
                    iClist[0:nC[i], i] = iC
                R = np.zeros(N)
                for i in range(N):
                    label = labels[i]
                    Nm = nC[label]
                    if Nm > 1:
                        iC = iClist[0:nC[label], label]
                        R[i] = np.sum(np.sqrt(np.sum((Xs[iC] - Xs[i]) ** 2, axis=1))) / (Nm - 1)
                    # else R[i]=0
                c = 0
                D = np.zeros(N)

                while c < N_iRDM:
                    I0 = set_update(m, I0, Xs, R, nC, iClist)
                    # for j in range(m):
                    #     iC = iClist[0:nC[j], j]  # indices of feature vectors in cluster #j
                    #     dist = np.sqrt(np.sum((Xs[iC].reshape(nC[j], nx, 1) - Xs[I0].T) ** 2, axis=1))
                    #     dist[:, j] = np.inf
                    #     D[iC] = np.min(dist, axis=1)
                    #     nstar = np.argmax(D[iC] - R[iC])
                    #     I0[j] = iC[nstar]
                    newI0 = np.sort(I0)
                    isnew = True
                    for i in range(c + 1):
                        isnew = not np.all(P[c] == newI0)
                        if not isnew:
                            break
                    if isnew:
                        c += 1
                        if c < N_iRDM:
                            P[c] = newI0
                    else:
                        break  # break while loop
                X_act[0:m] = X[I0]
                # acquire targets:
                if not isGeneratorFcn:
                    Y_act[0:m] = Y[I0]
                else:
                    Y_act[0:m] = generator_fcn(X[I0])
                Q_act[0:m] = np.all(np.isfinite(Y_act[0:m]),
                                    axis=1)  # targets that could not be acquired were labeled as Inf or NaN

            if retrain:
                if pred_type == 'classification':
                    if check_warm_start and hasattr(pred, 'classes_'):
                        # make sure we have the same classes, otherwise turn warm_start to false.
                        # Number of classes is unknown a priori and may change while acquiring new samples
                        if pred_warm_start:
                            if not np.all(pred.classes_ == np.unique(Y_act[Q_act])):
                                pred.warm_start = False

                if isQBC and unknown_constraint and np.any(~Q_act[0:m]):
                    # assume y(x)=yhat(x) on infeasible samples (this code could be made more
                    # efficient by exploting Yhat from the previous iteration...)
                    yy = Y_act[0:m].copy()
                    yyhat = pred.predict(X[0:m][~Q_act[0:m]])
                    if ny == 1:
                        yyhat = yyhat.reshape(-1, 1)
                    yy[0:m][~Q_act[0:m]] = yyhat
                else:
                    yy = Y_act[0:m]

                # train predictor on feasible samples only
                if ny == 1:
                    pred.fit(X_act[0:m][Q_act[0:m]], Y_act[0:m][Q_act[0:m]].reshape(-1))
                else:
                    pred.fit(X_act[0:m][Q_act[0:m]], Y_act[0:m][Q_act[0:m]])

                if pred_type == 'classification':
                    if check_warm_start:
                        pred.warm_start = pred_warm_start
                if isQBC:
                    # create N_qbc subsets of feasible samples and fit a predictor on each subset.
                    nn = np.arange(0, nfeas)
                    if isQBCleaveout:
                        jj = nn[np.random.permutation(nfeas)]
                        nleftout = int(np.floor(nfeas / N_qbc))  # number of samples left out
                    for j in range(N_qbc):
                        if isQBCbootstrap:
                            ii = nn[np.random.random_integers(0, high=nfeas - 1, size=nfeas)]  # bootstrap #j
                        elif isQBCleaveout:
                            hh = np.ones(nfeas, dtype=bool)
                            hh[j * nleftout:min((j + 1) * nleftout, nfeas)] = False
                            ii = jj[hh]  # subset #j
                        else:
                            raise Exception('QBC subset generation method is undefined')
                        if pred_type == 'classification':
                            if check_warm_start and hasattr(pred, 'classes_'):
                                if pred_warm_start:
                                    if not np.all(pred.classes_ == np.unique(yy[ii])):
                                        pred.warm_start = False
                        if ny == 1:
                            preds[j].fit(X_act[0:m][Q_act[0:m]][ii], Y_act[0:m][Q_act[0:m]][ii].reshape(-1))
                        else:
                            preds[j].fit(X_act[0:m][Q_act[0:m]][ii], Y_act[0:m][Q_act[0:m]][ii])

            print(thedelete, end="")

            if isGeneratorFcn:
                Y_score = Y_act[Q_act]
                X_score = X_act[Q_act]

            if pred_type == 'classification':
                score_type = "Accuracy"
                score_train = accuracy_score(Y_score, pred.predict(X_score)) * 100
                if isTest:
                    score_test = accuracy_score(Y_test, pred.predict(X_test)) * 100
            else:
                score_type = "RMSE"
                score_train = np.sqrt(mean_squared_error(Y_score, pred.predict(X_score)))
                if isTest:
                    score_test = np.sqrt(mean_squared_error(Y_test, pred.predict(X_test)))

            if verbose == 2:
                print("%s score = %5.5f (entire pool)" % (score_type, score_train), end="")
                if isTest:
                    print(", %5.5f (test data)" % score_test, end="")
                print("")
            elif verbose == 1:
                thestring = "N = %3d/%3d: score = %9s " % (m, maxevals, "%5.5f" % score_train) + '(training)'
                if isTest:
                    thestring = thestring + ' '
                    thestring = thestring + "%9s " % ("%5.5f" % score_test) + '(test)'

                print('%s' % thestring, end="")

                thedelete = '\b' * (len(thestring))

        else:
            if train_interval > 1 and verbose == 2:
                print("o", end="")

        scores_train[m - 1] = score_train
        scores_test[m - 1] = score_test

        m += 1

        if m < N and not isiRDM:
            # Optimize feature vector
            if not isRandom:
                thetype = (pred_type == 'classification')

                if isGreedy_x:
                    ff = -Dmin
                elif isGreedy_xy:
                    if ny == 1:
                        Yhat[~used] = pred.predict(X[~used]).reshape(-1, 1)
                        dy = (Y_act[Q_act].reshape(-1, 1) - Yhat[~used].reshape(1,
                                                                                -1)) ** 2  # matrix containing all distances in y-space
                    else:
                        nfeas = np.sum(Q_act)
                        Yhat[~used] = pred.predict(X[~used])
                        dy = np.sum((Y_act[Q_act].reshape(nfeas, ny, -1) - Yhat[~used].T) ** 2, axis=1)
                    dymin = np.min(dy, axis=0)
                    ff = np.zeros(N)
                    ff[~used] = -Dmin[~used] * dymin
                elif isQBC:
                    if ny == 1:
                        y = np.zeros((N_qbc, N))
                        for j in range(N_qbc):
                            y[j, ~used] = preds[j].predict(X[~used])
                        ff = -np.var(y, axis=0)  # this will be zero at used points
                    else:
                        y = np.zeros((N_qbc, N, ny))  # 3D matrix
                        for j in range(N_qbc):
                            y[j, ~used, :] = preds[j].predict(X[~used])
                        ymean = np.mean(y, axis=0)  # 2D matrix
                        ff = -np.sum(np.sum((y - ymean) ** 2, axis=0), axis=1)

                elif isIDEAL:
                    ff = np.zeros(N)

                    if ny == 1:
                        Yhat[~used] = pred.predict(X[~used]).reshape(-1, 1)
                    else:
                        Yhat[~used] = pred.predict(X[~used])

                    dY2 = (2 * Yscale) ** 2
                    # Evaluate the acquisition function. This is only required for ~used samples,
                    # but computing it for the entire pool in one shot is computationally faster.
                    for i in range(ny):
                        if not unknown_constraint:
                            ff -= np.sum((W[:, 0:m - 1] / SW.reshape(-1, 1)) * (
                                    (Yhat[:, i, np.newaxis] - Y_act[0:m - 1, i]) ** 2), axis=1) / dY2[i]
                        else:
                            ff -= np.sum((W[:, 0:m - 1][:, Q_act[0:m - 1]] / SW.reshape(-1, 1)) *
                                         ((Yhat[:, i, np.newaxis] - Y_act[0:m - 1, i][Q_act[0:m - 1]]) ** 2), axis=1) / \
                                  dY2[i]

                    if delta > 0:
                        ff -= delta * Z

                    if isloss:
                        ff = loss(X, Yhat) * ff

                if useDensity:
                    # ff /= -np.min(ff) # makes acquisition between -1 and 0
                    # ff += Dens
                    ff *= Dens

                ff[used] = np.inf  # this is to avoid selecting used samples

                ind = np.argmin(ff)
                xs = Xs[ind]
            else:
                # Get a random sample
                ind = random_indices[used_samples]
                used_samples += 1
                xs = Xs[ind]

            x = Xbias + Xscale * xs

            if m <= maxevals:
                # Acquire new sample

                # All samples are feasible wrt known constraints, no need to check them
                if not isGeneratorFcn:
                    y = Y[ind]
                else:
                    y = generator_fcn(x)
                I_act[m - 1] = ind
                used[ind] = True

                q = np.all(np.isfinite(y))

                X_act[m - 1] = x
                Y_act[m - 1] = y
                Xs_act[m - 1] = xs
                Q_act[m - 1] = q
                if q:
                    Ymax = np.maximum(Ymax, y)
                    Ymin = np.minimum(Ymin, y)
                    Yscale = (Ymax - Ymin) / 2.
                    nfeas += 1

                if not isRandom:
                    d = np.sum((Xs - xs) ** 2, axis=-1)
                    if isIDEAL:
                        # Update IDW functions
                        W[0:ind, m - 1] = np.exp(-d[0:ind]) / d[0:ind]
                        W[ind + 1:, m - 1] = np.exp(-d[ind + 1:]) / d[ind + 1:]
                        SW += W[:, m - 1]
                        if delta > 0:
                            SiD[0:ind] += 1. / d[0:ind]
                            SiD[ind + 1:] += 1. / d[ind + 1:]
                            Z[0:ind] = np.arctan(1. / SiD[0:ind]) * pi2
                            Z[ind + 1:] = np.arctan(1. / SiD[ind + 1:]) * pi2
                    else:
                        Dmin = np.minimum(Dmin, d)

    if verbose == 1:
        print("")

    if isiRDM:
        Ymax = np.max(Y_act[0:maxevals][Q_act[0:maxevals]], axis=0)
        Ymin = np.min(Y_act[0:maxevals][Q_act[0:maxevals]], axis=0)
        ii = (Ymax - Ymin < 1.e-8)
        Ymax[ii] += 1.e-8
        # Compute scaling factors for targets, to have -1 <= (y-Ybias)/Yscale <= 1
        # Ybias=(Ymax+Ymin)/2.
        Yscale = (Ymax - Ymin) / 2.

    samples = {'X_act': X_act, 'Y_act': Y_act, 'Q_act': Q_act, 'I_act': I_act,
               'Xbias': Xbias, 'Xscale': Xscale, 'Yscale': Yscale, 'init_evals': init_evals}
    scores = {'training': scores_train, 'test': scores_test}

    return pred, samples, scores
