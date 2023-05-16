# -*- coding: utf-8 -*-
"""
IDEAL - Inverse-Distance based Exploration for Active Learning

(C) 2022 A. Bemporad, April 14, 2022
    Revised by A. Bemporad, October 26, 2022
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd
from sklearn import preprocessing
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.svm import SVR
import ideal

np.random.seed(0)  # for reproducibility of results

#############################
# Choose example here below:
#############################
#example = "ideal"  # (regression) toy 1d problem
example = 'auto-mpg'  # (regression) https://archive.ics.uci.edu/ml/datasets/auto+mpg
#example = "iris"  # (classification) https://archive.ics.uci.edu/ml/datasets/Iris
#############################

# defaults:
verbose = 1
X_test = []
Y_test = []
loss = []
unknown_constraint = False  # no unknown constraints are present
known_constraint_fcn = None  # no known constraints are present
N_qbc = None
qbc_method = None
N_iRDM=None

plt.close('all')
plt.figure()

if example=="ideal" or example=='auto-mpg':
    exps = np.arange(0, 6).astype(int)
else:
    exps = [0,1,2,5]

for exp in exps:
    if exp == 0:
        # IDEAL method (active learning)
        method='ideal'
        init_method='kmeans'
    elif exp == 1:
        # Random sampling (passive learning)
        method='random'
        init_method='random'
    elif exp == 2:
        # Greedy sampling in feature-vector space (passive learning)
        method='greedy_x'
        init_method='greedy'
    elif exp == 3:
        # Greedy sampling in feature-vector and target spaces (active learning)
        method='greedy_xy'
        init_method='greedy'
    elif exp == 4:
        # Query by committee
        method='qbc'
        init_method='random'
        N_qbc = 5 # number of predictor in the committee
        qbc_method = 'bootstrap'
    elif exp == 5:
        # iRDM
        method='irdm'
        init_method='kmeans'
        N_iRDM = 5 # max number of iRDM iterations

    if example == 'ideal':
        def fun(X):
            y = X ** 4 * np.sin((X ** 2) / 3.) ** 2
            if unknown_constraint:
                # make y(x) undefined for |x|<1
                y[np.abs(X) < 1] = np.inf
            return y
        ny = 1

        Xmin = -3.
        Xmax = 3.
        Nf = 1000  # large number, assuming that the function can be sampled arbitrarily
        nx = 1
        X = np.arange(Xmin, Xmax, (Xmax - Xmin) / Nf).reshape(-1, 1)
        Y = fun # just provide the function, not the targets

        unknown_constraint = False

        # Dataset to measure prediction performance
        X_test = np.random.rand(100, 1) * (Xmax - Xmin) + Xmin
        Y_test = Y(X_test)

        if unknown_constraint:
            isFeasible = np.isfinite(Y_test)
            X_test = X_test[isFeasible].reshape(-1, 1)
            Y_test = Y_test[isFeasible].reshape(-1, 1)

        #def loss(X,Y):
        #    return np.sum(1. + np.abs(X), axis=1) # emphasize vectors x with larger magnitude

        n_init = 10  # first samples picked up samples to train first predictor are
        #           those closest to centroids obtained by K-means
        delta = 5.
        density_weight = 0.0
        pred_type = "regression"

        maxevals = 40
        T_train = 1  # re-train every T_train samples

        pred = MLPRegressor(alpha=1e-2, hidden_layer_sizes=(5,5), activation='logistic', solver='lbfgs',
                            random_state=None, max_iter=50000, warm_start=False, tol=1e-8,
                            max_fun=100000)

    elif example == 'auto-mpg':
        dataset = pd.read_csv("../datasets/UCI_datasets/auto-mpg.data", sep='\s+', header=None)
        dataset = dataset[dataset[3] != "?"]
        Y = dataset.iloc[:, 0].values.astype('float')
        X = dataset.iloc[:, 1:7].values.astype('float')
        scaler_x = preprocessing.StandardScaler().fit(X)
        X = scaler_x.transform(X)

        maxevals = 150
        n_init = 20
        delta = 5.0
        density_weight = 0.0
        T_train = 1  # re-train every T_train samples

        #pred = MLPRegressor(alpha=0.01, hidden_layer_sizes=(5, 5), activation='logistic', solver='lbfgs',
        #                    random_state=None, max_iter=50000, warm_start=False, tol=1e-6,
        #                    max_fun=50000)
        pred = SVR(kernel='rbf', C=50, epsilon=0.05)

        pred_type = "regression"

        Ymin = np.min(Y)
        Ymax = np.max(Y)
        Y = (Y - (Ymin + Ymax) / 2.) / (Ymax - Ymin) * 2.


    elif example == 'iris':
        # https://archive.ics.uci.edu/ml/datasets/Iris
        dataset = pd.read_csv("datasets/iris.data", header=None)
        X = dataset.iloc[:, 0:4].values
        Y = dataset.iloc[:, 4].values
        scaler_x = preprocessing.StandardScaler().fit(X)
        X = scaler_x.transform(X)

        maxevals = 60
        alpha = 0.01
        hidden_layer_sizes = (10, 10, 10)
        n_init = 20
        delta = 5.0
        density_weight = 0.0
        T_train = 1  # re-train every T_train samples

        pred = MLPClassifier(alpha=alpha, hidden_layer_sizes=hidden_layer_sizes,
                             activation='logistic', solver='lbfgs',
                             random_state=None, max_iter=10000, warm_start=False, tol=1e-6,
                             max_fun=50000)

        pred_type = "classification"

    else:
        raise Exception('Unknown example')

    data = {"X": X, "Y": Y, "X_test": X_test, "Y_test": Y_test}

    if example == 'ideal':
        data["ny"] = ny

    print("%10s: " % method, end="")

    t1 = time.time()
    trained_pred, samples, scores = ideal.ideal_training(data, pred, pred_type,
                                                         n_init, maxevals, train_interval=T_train,
                                                         delta=delta, method=method, init_method=init_method,
                                                         qbc_method=qbc_method, N_qbc=N_qbc, N_iRDM=N_iRDM,
                                                         verbose=verbose, loss=loss,
                                                         unknown_constraint=unknown_constraint,
                                                         known_constraint_fcn=known_constraint_fcn,
                                                         density_weight=density_weight)
    t1 = time.time() - t1
    print('Elapsed time: %5.4f' % t1)

    if example == "ideal":
        score_train = scores["test"]
    else:
        score_train = scores["training"]

    X_act = samples["X_act"]
    Y_act = samples["Y_act"]
    Q_act = samples["Q_act"]

    plt.figure(1)
    if pred_type == 'regression':
        plt.semilogy(np.arange(n_init, maxevals) + 1, score_train[n_init:maxevals], linewidth=3,
                     label=method)
        plt.title('RMSE')
    else:
        plt.plot(np.arange(n_init, maxevals) + 1, score_train[n_init:maxevals], linewidth=3, label=method)
        plt.title('Accuracy')
    plt.legend()
    plt.xlabel('queries')
    plt.draw()

    if exp == 0 and example == "ideal":
        plt.figure(2)
        isort = np.argsort(X, axis=0).flatten("c")
        Yhat = trained_pred.predict(X)
        plt.plot(X[isort], Y(X[isort]), linewidth=3, label=r'$y(x)$')
        plt.plot(X[isort], Yhat[isort], linewidth=3, label=r'$\hat y(x)$')
        plt.legend()
        plt.grid()
        plt.xlabel(r'$x$')
        plt.draw()

plt.figure(1)
plt.grid()
plt.show()
