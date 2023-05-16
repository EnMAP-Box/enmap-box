# -*- coding: utf-8 -*-
"""
IDEAL - Inverse-Distance based Exploration for Active Learning

(C) 2022 A. Bemporad, October 26, 2022
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPRegressor
import ideal

np.random.seed(0)  # for reproducibility of results

plt.close('all')
plt.figure()

Xmin = -3.
Xmax = 3.
Nf = 1000  # large number, assuming that the function can be sampled arbitrarily
nx = 1

fun = lambda X: X ** 4 * np.sin((X ** 2) / 3.) ** 2

X_pool = np.arange(Xmin, Xmax, (Xmax - Xmin) / Nf).reshape(-1, 1)
Y_pool = fun(X_pool)

X_test = np.random.rand(100, 1) * (Xmax - Xmin) + Xmin
Y_test = fun(X_test)

n_init = 4  # first samples picked up samples to train first predictor are
#           those closest to centroids obtained by K-means
delta = 5.
pred_type = "regression"

maxevals = 30
T_train = 1  # re-train every T_train samples

pred = MLPRegressor(alpha=1e-2, hidden_layer_sizes=(5, 5), activation='logistic', solver='lbfgs',
                    random_state=None, max_iter=50000, warm_start=False, tol=1e-8,
                    max_fun=100000)

data = {"X": X_pool, "Y": Y_pool, "X_test": X_test, "Y_test": Y_test}

trained_pred, samples, scores = ideal.ideal_training(data, pred, pred_type, delta=5.,
                                                     n_init=n_init, maxevals=maxevals, method='ideal', verbose=1)
X_act = samples["X_act"]
Y_act = samples["Y_act"]

plt.figure(1)
plt.semilogy(np.arange(n_init, maxevals) + 1, scores["test"][n_init:maxevals], linewidth=3)
plt.title('RMSE on test data')
plt.grid()
plt.xlabel('queries')
plt.draw()
plt.show()

plt.figure(2)
plt.plot(X_pool, Y_pool, linewidth=3.0, label='true target')
plt.plot(X_pool, pred.predict(X_pool), linewidth=3.0, label='predicted target')
plt.scatter(samples["X_act"], samples["Y_act"], label='acquired samples')
plt.legend()
plt.grid()
plt.draw()
plt.show()
