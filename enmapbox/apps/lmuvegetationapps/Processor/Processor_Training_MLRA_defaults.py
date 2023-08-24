# -*- coding: utf-8 -*-
"""
***************************************************************************
    Processor_Training_MLRA_defaults.py - LMU Agri Apps - Machine learning based spectroscopic image inversion of
    PROSAIL parameters - CORE
    -----------------------------------------------------------------------
    begin                : 08/2023
    copyright            : (C) 2023 Matthias Wocher
    email                : m.wocher@lmu.de

***************************************************************************
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software. If not, see <http://www.gnu.org/licenses/>.
***************************************************************************
"""

from scipy.stats import expon, reciprocal
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel as C


class MLRA_defaults:
    # Artificial Neural Network
    ANN = {
        'default': {
            'hidden_layer_sizes': (100,),
            'activation': 'logistic',
            'solver': 'lbfgs',
            'alpha': 1.0,  # L2 penalty (regularization term) parameter.
            'learning_rate': 'constant',
            'max_iter': 5000
        },
        'param_dist': {
            'hidden_layer_sizes': [(50, 50, 50), (50, 100, 50), (100,)],
            'activation': ['tanh', 'relu', 'logistic'],
            'solver': ['sgd', 'adam', 'lbfgs'],
            'alpha': reciprocal(0.01, 10),  # L2 penalty (regularization term) parameter.
            'learning_rate': ['constant', 'adaptive'],
            'max_iter': [500, 1000, 2000, 5000]
        },
        'LIDF': {
            'hidden_layer_sizes': (100,),
            'activation': 'tanh',
            'solver': 'lbfgs',
            'alpha': 10,  # L2 penalty (regularization term) parameter.
            'learning_rate': 'constant',
            'max_iter': 5000
        },
        'cab': {
            'hidden_layer_sizes': (100,),
            'activation': 'tanh',
            'solver': 'adam',
            'alpha': 0.01,  # L2 penalty (regularization term) parameter.
            'learning_rate': 'constant',
            'max_iter': 2000
        },
        'cm': {
            'hidden_layer_sizes': (100,),
            'activation': 'logistic',
            'solver': 'lbfgs',
            'alpha': 0.1,  # L2 penalty (regularization term) parameter.
            'learning_rate': 'constant',
            'max_iter': 1000
        }
    }
    # Gaussian Process Regression
    GPR = {
        'default': {
            'kernel': C(1.0, constant_value_bounds="fixed")
                      * RBF(length_scale=1.0, length_scale_bounds=(1e-5, 1e5))
                      + WhiteKernel(noise_level=1.0, noise_level_bounds="fixed"),
            'alpha': 1e-10,
            'random_state': 42
        },
        'param_dist': {
            "alpha": expon(scale=1),
            "kernel__k1__k1__constant_value": expon(scale=1),
            "kernel__k1__k2__length_scale": expon(scale=1),
            "kernel__k2__noise_level": expon(scale=1)
        }
    }

    RFR = {
        'default': {
            'n_estimators': 100,  # The number of trees in the forest.
            'criterion': 'mse',  # The function to measure the quality of a split.
            'max_depth': None,  # The maximum depth of the tree.
            'min_samples_split': 2,  # The minimum number of samples required to split an internal node.
            'min_samples_leaf': 1,  # The minimum number of samples required to be at a leaf node.
            },
        'param_dist': {
            'n_estimators': [10, 50, 100, 200],
            'max_features': ['auto', 'sqrt', 'log2'],
            'max_depth': [None, 10, 20, 30, 40, 50],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'bootstrap': [True, False]
        }
    }
    # Support Vector Regression
    SVR = {
        'default': {
            'kernel': 'rbf',  # Specifies the kernel type to be used in the algorithm.
            'gamma': 'scale',  # Kernel coefficient for ‘rbf’, ‘poly’ and ‘sigmoid’.
            'C': 1000.0,
            # Regularization parameter. The strength of the regularization is inversely proportional to C.
            'epsilon': 0.1,  # Epsilon in the epsilon-SVR model.
            # Add more parameters as needed.
            },
        'param_dist': {
            'C': reciprocal(1, 1000),
            'epsilon': [0.01, 0.1, 1],
            'kernel': ['rbf', 'sigmoid'],
            'gamma': ['scale', 'auto'] + list(reciprocal(0.01, 1).rvs(size=1000))
        }
    }
    # Kernel Ridge Regression
    KRR = {
        'default': {
            'alpha': 0.1,  # Regularization strength; must be a positive float.
            'kernel': 'rbf',  # Specifies the kernel type to be used in the algorithm.
            'gamma': None,  # Kernel coefficient for ‘rbf’, ‘poly’ and ‘sigmoid’.
            'degree': 4,  # Degree for ‘poly’ kernel. Ignored by all other kernels.
            'coef0': 2  # Independent term in ‘poly’ and ‘sigmoid’.
            # Add more parameters as needed.
        },
        'param_dist': {
            'alpha': [0.1, 0.5, 1, 2],
            'kernel': ['linear', 'rbf', 'polynomial', 'sigmoid'],
            'degree': [2, 3, 4],  # Relevant for polynomial kernel
            'coef0': [0.1, 0.5, 1, 2]  # Useful for polynomial and sigmoid kernels
        }
    }
    # Gradient Boosting Regression
    GBR = {
        'default': {
            'n_estimators': 100,  # The number of boosting stages to perform.
            'learning_rate': 0.1,  # Learning rate shrinks the contribution of each tree by learning_rate.
            'max_depth': 3,  # Maximum depth of the individual regression estimators.
            'subsample': 1.0,  # The fraction of samples to be used for fitting the individual base learners.
            'random_state': 42  # Controls the randomness of the estimator.
            # Add more parameters as needed.
        },
        'param_dist': {
            'n_estimators': [50, 100, 200],
            'learning_rate': [0.01, 0.05, 0.1],
            'max_depth': [3, 4, 5, 6],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'subsample': [0.8, 0.9, 1.0],
            'max_features': ['auto', 'sqrt', 'log2']
        }
    }


# settings according to Danner et al. (2021): old implementation
# if var == "LIDF":  # hyperparameters best suited to estimate the ALIA
#     self.ann_activation = 'tanh'  # logistic, relu, identity, tanh
#     self.ann_solver = 'lbfgs'  # adam, lbfgs, sgd
#     self.ann_alpha = 10.0
#     self.ann_max_iter = 10000  # 5000
# elif var == "cab":  # hyperparameters best suited to estimate Cab
#     self.ann_activation = 'tanh'  # logistic, relu, identity, tanh
#     self.ann_solver = 'adam'  # adam, lbfgs, sgd
#     self.ann_alpha = 0.01
#     self.ann_max_iter = 10000  # 2000
# elif var == "cm":  # hyperparameters best suited to estimate LMA
#     self.ann_activation = 'logistic'  # logistic, relu, identity, tanh
#     self.ann_solver = 'lbfgs'  # adam, lbfgs, sgd
#     self.ann_alpha = 0.1
#     self.ann_max_iter = 10000  # 1000
# else:  # hyperparameters best suited to estimate LAI and all others
#     self.ann_activation = 'logistic'  # logistic, relu, identity, tanh
#     self.ann_solver = 'lbfgs'  # adam, lbfgs, sgd
#     self.ann_alpha = 1.0
#     self.ann_max_iter = 10000  # 5000


