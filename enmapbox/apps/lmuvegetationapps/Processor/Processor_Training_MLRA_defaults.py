# -*- coding: utf-8 -*-
"""
***************************************************************************
    Processor_Training_MLRA_defaults.py - LMU Agri Apps
    -----------------------------------------------------------------------
    begin                : 08/2023
    copyright            : (C) 2024 Matthias Wocher
    email                : m.wocher@iggf.geo.uni-muenchen.de

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
    along with this software. If not, see <https://www.gnu.org/licenses/>.
***************************************************************************
"""

from scipy.stats import expon, reciprocal
from sklearn.gaussian_process import kernels


class MLRA_defaults:
    """
    MLRA defaults and pretested variable specific settings
    'param_dist': default hyperparameter settings for RandomizedSearchCV/GridSearchCV
    ANN settings acc. to Danner et al. 2021
    GPR settings acc. to GridSearchCV by Wocher (2023)
    """
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
            'alpha': [0.01, 0.1, 1.0, 10.0],  # L2 penalty (regularization term) parameter.
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
            'kernel': kernels.ConstantKernel(1.0) * kernels.Matern(length_scale=1, nu=1.5),
            # kernels.ConstantKernel(1.0) *
            # 1.0 * kernels.RBF(length_scale=1.0, length_scale_bounds=(1e-5, 1e5)) +
            #       kernels.WhiteKernel(noise_level=1.0, noise_level_bounds="fixed"),
            'alpha': 1.0,
            'n_restarts_optimizer': 10,
            'random_state': 42
            # 'warm_start': True
        },
        'param_dist': {
            'kernel': [kernels.ConstantKernel(1.0) *
                       kernels.Matern(length_scale=v, nu=nu)
                       for v in [0.01, 0.1, 1.0, 10, 100] for nu in [0.5, 1.5, 2.5, float('inf')]],
            # **kernels.ConstantKernel(1.0) *
            # [1.0 * kernels.RBF(length_scale=v) + kernels.WhiteKernel(noise_level=1.0, noise_level_bounds=(1e-5, 1e5)) for v in [0.01, 0.1, 1.0, 10, 100]]
            "alpha": [0.001, 0.01, 0.1, 1.0],
            # 'random_state': 42
        },
        'cab': {
            'kernel': kernels.ConstantKernel(1.0) * kernels.Matern(length_scale=10, nu=2.5),
            'alpha': 1.0,
            'n_restarts_optimizer': 10,
        },
        'LAI': {
            'kernel': kernels.ConstantKernel(1.0) * kernels.Matern(length_scale=1, nu=2.5),
            'alpha': 0.1,
            'n_restarts_optimizer': 10,
        },
        'AGBdry': {
            'kernel': kernels.ConstantKernel(1.0, constant_value_bounds=(1e-5, 1e7)) *
                      kernels.Matern(length_scale=10, length_scale_bounds=(1e-5, 1e7), nu=0.5) +
                      kernels.WhiteKernel(noise_level=1.0, noise_level_bounds=(1e-5, 1e7)),
            'alpha': 1.0,
            'n_restarts_optimizer': 10,
        },
        'AGBfresh': {
            'kernel': kernels.ConstantKernel(1.0, constant_value_bounds=(1e-5, 1e7)) *
                      kernels.Matern(length_scale=10, length_scale_bounds=(1e-5, 1e7), nu=0.5) +
                      kernels.WhiteKernel(noise_level=1.0, noise_level_bounds=(1e-5, 1e7)),
            'alpha': 1.0,
            'n_restarts_optimizer': 10,
        },
        'CWC': {
            'kernel': kernels.ConstantKernel(1.0) * kernels.Matern(length_scale=1, nu=1.5),
            'alpha': 1.0,
            'n_restarts_optimizer': 10,
        },
        'Nitrogen': {
            'kernel': kernels.ConstantKernel(1.0, constant_value_bounds=(1e-5, 1e7)) *
                      kernels.Matern(length_scale=1, length_scale_bounds=(1e-5, 1e7), nu=2.5) +
                      kernels.WhiteKernel(noise_level=1.0, noise_level_bounds=(1e-5, 1e7)),
            'alpha': 1.0,
            'n_restarts_optimizer': 10,
        },
        'Carbon': {
            'kernel': kernels.ConstantKernel(1.0) * kernels.Matern(length_scale=10, nu=0.5),
            'alpha': 1.0,
            'n_restarts_optimizer': 10,
        }
    }
    # Random Forest Regression
    RFR = {
        'default': {
            'n_estimators': 1000,  # The number of trees in the forest.
            'criterion': 'squared_error',  # The function to measure the quality of a split.
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
            'C': [1, 10, 100, 1000],
            'epsilon': [0.01, 0.1, 1],
            'kernel': ['rbf', 'sigmoid'],
            'gamma': ['scale', 'auto'] + [0.01, 0.1, 1.0]
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
