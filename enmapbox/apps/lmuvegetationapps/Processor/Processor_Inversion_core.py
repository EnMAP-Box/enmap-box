# -*- coding: utf-8 -*-
"""
***************************************************************************
    Processor_Inversion_core.py - LMU Agri Apps - Machine Learning Algorithms - Training and Inversion of PROSAIL
    parameters for mapping of spectroscopic imagery - CORE
    -----------------------------------------------------------------------
    begin                : 09/2020
    copyright            : (C) 2024 Matthias Wocher; Martin Danner
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
    along with this software. If not, see <http://www.gnu.org/licenses/>.
***************************************************************************

This script uses Machine Learning (ML) algorithms to predict / estimate PROSAIL parameters
from spectral images. This _core module can do both training and prediction, the GUIs are split into different scripts.

"""
import os
import sys
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
# from sklearn.exceptions import ConvergenceWarning
# warnings.filterwarnings('ignore', category=ConvergenceWarning)

if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore" # Also affect subprocesses


from _classic.hubflow.core import *
import numpy as np
from PyQt5 import QtCore

from lmuvegetationapps.Processor.Processor_Training_MLRA_defaults import MLRA_defaults

from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process import kernels
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.kernel_ridge import KernelRidge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import RandomizedSearchCV

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

from sklearn.metrics import pairwise_distances
from sklearn.model_selection import KFold, train_test_split
# from sklearn.linear_model import LinearRegression
from sklearn.model_selection import check_cv
from sklearn.model_selection import cross_val_predict
from sklearn.base import is_classifier

from sklearn.utils._testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning

import joblib
from joblib import Parallel, delayed

def squeeze_first_dim(arr):
  """Squeezes a numpy array only if its first dimension is 1.
  Args:
    arr: The numpy array to be squeezed.
  Returns:
    The squeezed array if the first dimension was 1, otherwise the original array.
  """
  if arr.shape[0] == 1:
    return np.squeeze(arr, axis=0)
  else:
    return arr
def max_euclidean_distances(unlabeled, train, n):
    """
    Find n indices from unlabeled that are furthest from train using squared Euclidean distance.
    Parameters:
    - unlabeled, train (np.array): Data arrays.
    - n (int): Number of indices to select.
    Returns:
    - list: Indices of unlabeled that are furthest from train.
    """
    # Compute all pairwise distances
    all_distances = pairwise_distances(unlabeled, train, metric='sqeuclidean')
    max_n_indices = np.argpartition(all_distances.flatten(), -n)[-n:]
    max_n_2d_indices = np.unravel_index(max_n_indices, all_distances.shape)
    indices_arr1 = max_n_2d_indices[0]
    # Return the n maximum distances indices as a list
    # Convert to set and back to list to remove duplicates
    # unique_indices = list(set(indices_arr1.tolist()))
    return indices_arr1.tolist()

@ignore_warnings(category=ConvergenceWarning)
def pool_active_learning(X_train, y_train, X_unlabeled, model, n, k, n_jobs):
    """
    Implements the Pool Active Learning (PAL) approach.

    Parameters:
    - X_train (np.array): Original training data.
    - y_train (np.array): Original training labels.
    - X_unlabeled (np.array): Data for which the labels are to be queried.
    - model: The regressor model. Assumes that the model has `.fit` and `.predict` methods.
    - n (int): Number of instances to query.
    - n_models (int): Number of models to be trained on different subsets.

    Returns:
    - list: Indices of instances to be queried.
    """

    def train_and_predict(subset_indices):
        X_subset = X_train[subset_indices]
        y_subset = y_train[subset_indices]
        model.fit(X_subset, y_subset)
        return model.predict(X_unlabeled)

    n_samples = X_train.shape[0]
    subset_size = n_samples // k

    # Here, we will train the model on different subsets from the original training set
    # and collect predictions for the unlabeled data.
    # predictions = []

    # deprecated non-parallelized version of fit/predict the random subsets
    # for i in range(k):
    #     # Create random subsets of the original training data
    #     if mode == 'random':
    #         subset_indices = np.random.choice(n_samples, size=subset_size, replace=False)
    #     else:
    #         break
    #     X_subset = X_train[subset_indices]
    #     y_subset = y_train[subset_indices]
    #     # Train the model on the subset
    #     model.fit(X_subset, y_subset)
    #     # Predict on the entire unlabeled set and store the predictions
    #     preds = model.predict(X_unlabeled)
    #     predictions.append(preds)

    subset_indices_list = [np.random.choice(n_samples, size=subset_size, replace=False) for _ in range(k)]

    # Parallelize the training and predicting steps
    predictions = Parallel(n_jobs=n_jobs)(delayed(train_and_predict)(subset) for subset in subset_indices_list)

    # Convert list of predictions into an array [n_samples, n_models]
    predictions_array = np.array(predictions).T
    # Calculate the variance for each instance across models
    variances = np.var(predictions_array, axis=1)
    # Get indices of instances with the highest variance
    top_indices = np.argsort(variances)[-n:]

    return top_indices.tolist()


def al_query(X_train, y_train, X_unlabeled, strategy, model, n=1, k=5, n_jobs=1):
    if strategy == "EBD":
        return max_euclidean_distances(X_unlabeled, X_train, n=n)
    elif strategy == 'PAL':
        # X_train: X[initial_idx]; X_unlabeled: remaining_X
        return pool_active_learning(X_train, y_train, X_unlabeled, model=model, n=n, k=k, n_jobs=n_jobs)
    # More strategies can be added here as elif conditions
    else:
        raise ValueError(f"Strategy {strategy} not recognized!")


# Class MLRATraining will only be used for training new models, not for predictions!
class MLRATraining:
    def __init__(self, main):
        self.m = main

    @staticmethod
    def cross_val_predict_with_std(X, y, model, cv=None):
        """
        Custom version of cross_val_predict that also computes prediction standard deviations (for GPRs).
        Only works for GaussianProcessRegressor; for other regressors, it behaves just like cross_val_predict.
        """
        if not isinstance(model, GaussianProcessRegressor):
            # Fall back to scikit-learn's cross_val_predict if we don't need std. dev.
            return cross_val_predict(model, X, y, cv=cv)

        cv = check_cv(cv, y, classifier=is_classifier(model))

        predictions = np.empty_like(y, dtype=float)
        stds = np.empty_like(y, dtype=float)

        for train, test in cv.split(X, y):
            model.fit(X[train], y[train])
            preds, sigmas = model.predict(X[test], return_std=True)
            predictions[test] = preds
            stds[test] = sigmas

        return predictions, stds

    @staticmethod
    def _fit(X, y, model):
        # fits ("trains") the model by assessing X (predictors, reflectances) and y (PROSAIL parameters)
        # So the result is a model that is ready to be used as in ".predict(new_x)"
        return model.fit(X, y)

    @staticmethod
    def _fit_insitu_or_testset(X, y, X_val, y_val, model):
        # fit a model on RTM-data but evaluate performance on insitu data or previous test set
        # (e.g. retraining case after AL)
        stds = []
        np.savetxt("C:\Data\Daten\Testdaten\LUT/x_train_retrain.txt", X, delimiter="\t")
        np.savetxt("C:\Data\Daten\Testdaten\LUT/y_train_retrain.txt", y, delimiter="\t")
        np.savetxt("C:\Data\Daten\Testdaten\LUT/x_test_retrain.txt", X_val, delimiter="\t")
        model.fit(X, y)
        if isinstance(model, GaussianProcessRegressor):
            predictions, stds = model.predict(X_val, return_std=True)
        else:
            predictions = model.predict(X_val)
        score = mean_squared_error(y_val, predictions, squared=False)

        yield {'type': 'result', 'model': model, 'performances': score, 'predictions': predictions, 'stds': stds,
               'X_val': X_val, 'y_val': y_val}

    @staticmethod
    def _fit_hyper(X, y, model, X_val=None, y_val=None, test_size=0.2):
        # fit a RandomSearchCV or GridSearchCV model -> model here is a wrapper
        stds = []
        # yield {"type": "progress", "progress": 0, "loop_counter": 1}
        if X_val is None:
            train_X, test_X, train_y, test_y = train_test_split(X, y, test_size=test_size, random_state=42)
        else:
            train_X, test_X, train_y, test_y = X, X_val, y, y_val

        model.fit(train_X, train_y)
        if isinstance(model, RandomizedSearchCV) and isinstance(model.best_estimator_, GaussianProcessRegressor):
            predictions, stds = model.best_estimator_.predict(test_X, return_std=True)
            # print(predictions)
        elif isinstance(model, GridSearchCV) and isinstance(model.best_estimator_, GaussianProcessRegressor):
            predictions, stds = model.best_estimator_.predict(test_X, return_std=True)
        else:
            predictions = model.best_estimator_.predict(test_X)
        best_hyperparams = model.best_params_
        best_score = model.best_score_
        yield {"type": "hyperparameters", "best_hyperparams": best_hyperparams, "best_score": best_score}
        score = mean_squared_error(test_y, predictions, squared=False)
        yield {'type': 'result', 'model': model, 'performances': score, 'predictions': predictions, 'stds': stds,
               'X_val': test_X, 'y_val': test_y}

    @staticmethod
    def _fit_split(X, y, model, split_method="train_test_split", kfolds=5, test_size=0.2):
        # basic model fit on train-test-split or on cross validation sets
        yield {"type": "progress", "progress": 0, "loop_counter": 1}
        if split_method == 'train_test_split':
            stds = []
            train_X, test_X, train_y, test_y = train_test_split(X, y, test_size=test_size)
            model.fit(train_X, train_y)
            if isinstance(model, GaussianProcessRegressor):
                predictions, stds = model.predict(test_X, return_std=True)
            else:
                predictions = model.predict(test_X)
            score = mean_squared_error(test_y, predictions, squared=False)
            model.fit(X, y)

            yield {'type': 'result', 'model': model, 'performances': score, 'predictions': predictions, 'stds': stds,
                   'X_val': test_X, 'y_val': test_y}

        elif split_method == 'kfold':
            # In the case of k-fold cross-validation, use cross_val_predict to get the predictions for each fold
            yield {"type": "progress", "progress": 0, "loop_counter": 1}  # Indicate start of process
            if isinstance(model, GaussianProcessRegressor):
                # If the model is a GaussianProcessRegressor, also get the standard deviations of the predictions
                predictions, stds = MLRATraining.cross_val_predict_with_std(X, y, model, cv=kfolds)
                score = mean_squared_error(y, predictions, squared=False)
                yield {"type": "progress", "progress": 100, "loop_counter": 1}  # Indicate end of process
                yield {'type': 'result', 'model': model, 'performances': score,
                       'predictions': predictions, 'stds': stds, 'X_val': X, 'y_val': y}
            else:
                # If the model is not a GaussianProcessRegressor, get the predictions without standard deviations
                predictions = cross_val_predict(model, X, y, cv=kfolds)
                score = mean_squared_error(y, predictions, squared=False)
                yield {"type": "progress", "progress": 100, "loop_counter": 1}  # Indicate end of process
                yield {'type': 'result', 'model': model, 'performances': score,
                       'predictions': predictions, 'X_val': X, 'y_val': y}

    @staticmethod
    def _split(X, y, split_method="train_test_split", kfolds=5, test_size=0.2, random_state=42):
        # split function for the internal active learning loop
        if split_method == "train_test_split":
            X_idx = range(len(X))
            X_train, X_test, y_train, y_test, X_idx_train, X_idx_test = train_test_split(
                X, y, X_idx, test_size=test_size, random_state=random_state)
            yield X_train, X_test, y_train, y_test, X_idx_train, X_idx_test
        elif split_method == "kfold":
            kf = KFold(n_splits=kfolds, random_state=random_state, shuffle=True)
            for train_index, test_index in kf.split(X, y):
                yield X[train_index], X[test_index], y[train_index], y[test_index], train_index, test_index
        else:
            raise ValueError(f"Unrecognized split method: {split_method}")

    @staticmethod
    def _al_loop_internal(X, y, model, init_percentage, query_strat='PAL', split_method="train_test_split", kfolds=5,
                          test_size=0.2, n_jobs=1):
        al_training_indices = []
        all_performances = []
        all_stds = []
        all_preds = []
        train_idx = []
        test_idx = []
        X_val, y_val = None, None
        loop_counter = 1
        for X_train, X_test, y_train, y_test, train_idx, test_idx in (
                MLRATraining._split(X, y, split_method=split_method, kfolds=kfolds, test_size=test_size)):
            # Get generator from _al_loop
            loop_gen = MLRATraining._al_loop(X_train, y_train, X_test, y_test, model,
                                             init_percentage=init_percentage, query_strat=query_strat, n_jobs=n_jobs)

            for output in loop_gen:
                # loop_gen is the yield dict output of _al_loop() and can be of 'type': 'result' or 'progress'
                if output['type'] == 'result':
                    al_training_indices.append(output['al_training_indices'])
                    all_performances.append(output['performances'])
                    if isinstance(model, GaussianProcessRegressor):
                        preds, stds = model.predict(output['X_val'], return_std=True)
                        all_stds.append(stds)
                        all_preds.append(preds)
                    else:
                        all_preds.append(model.predict(output['X_val']))
                    X_val = output['X_val']
                    y_val = output['y_val']
                else:
                    output['loop_counter'] = loop_counter
                    yield output
            loop_counter += 1

        np.savetxt("C:\Data\Daten\Testdaten\LUT/training_indices_AL_internal.txt", al_training_indices, delimiter="\t")

        yield {'type': 'result', 'model': model, 'al_training_indices': al_training_indices,
               'performances': all_performances, 'predictions': all_preds, 'stds': all_stds, 'X_val': X_val,
               'y_val': y_val, 'test_indices': test_idx, 'split_training_indices': train_idx}

    @staticmethod
    def _al_loop(X, y, X_val, y_val, model, init_percentage, query_strat, n_jobs):

        def get_random_choice(array, size, random_state=42):
            rng = np.random.default_rng(random_state)
            return rng.choice(range(len(array)), size=size, replace=False)

        init_percentage = init_percentage / 100
        # print("init_perc: " + str(init_percentage))
        n_samples = X.shape[0]
        n_init = round(init_percentage * n_samples)
        # print("n_init: " + str(n_init))
        initial_idx = get_random_choice(range(len(X)), size=n_init)  # random initial sampling

        al_training_indices = list(initial_idx)  # save the indices of n initial samples

        X_initial, y_initial = X[initial_idx], y[initial_idx]  # select n initial samples from X

        model.fit(X_initial, y_initial)  # fit the model on n initial samples

        performances = []  # initialize performances list

        initial_pred = model.predict(X_val)  # predict first model on validation set (insitu or test split)
        best_score = mean_squared_error(y_val, initial_pred, squared=False)  # calculate first score (RMSE)
        performances.append(best_score)  # save first RMSE

        # update remaining indices -> all indices (n_samples) minus current training indices
        remaining_indices = np.setdiff1d(np.arange(n_samples), al_training_indices)

        total_remaining = len(remaining_indices)  # count remaining indices
        last_printed = -1

        # here the actual al loop starts
        for i in range(len(remaining_indices)):

            remaining_X = X[remaining_indices]  # get remaining X
            query_indices = al_query(X_train=X[initial_idx], y_train=y[initial_idx],
                                     X_unlabeled=remaining_X, model=model, strategy=query_strat,
                                     n_jobs=n_jobs)  # X_raw[initial_idx])
            chosen_indices = remaining_indices[query_indices]

            X_initial = np.concatenate((X_initial, X[chosen_indices]))
            y_initial = np.concatenate((y_initial, y[chosen_indices]))
            al_training_indices.extend(chosen_indices)

            model.fit(X_initial, y_initial)

            pred = model.predict(X_val)
            score = mean_squared_error(y_val, pred, squared=False)
            performances.append(score)

            progress = (total_remaining - len(remaining_indices)) / total_remaining * 100
            if int(progress) % 5 == 0 and int(progress) != last_printed:
                # print('Progress: {:.0f}%'.format(progress))
                last_printed = int(progress)
                yield {'type': 'progress', 'progress': progress}

            if score > best_score:
                X_initial = np.delete(X_initial, -len(query_indices), axis=0)
                y_initial = np.delete(y_initial, -len(query_indices), axis=0)
                al_training_indices.pop(-len(query_indices))
                performances.pop()
            else:
                best_score = score
                initial_idx = np.concatenate((initial_idx, chosen_indices))  #
                # print('RMSE: {:.4f}'.format(best_score))

            # TODO: implement case when n query is > 1 -> Avoid deletion of more than available samples:
            # if score > best_score:
            #     num_to_delete = min(len(query_indices), len(X_initial))
            #     X_initial = np.delete(X_initial, -num_to_delete, axis=0)
            #     y_initial = np.delete(y_initial, -num_to_delete, axis=0)
            #     for _ in range(num_to_delete):
            #         al_training_indices.pop()
            #     performances.pop()

            remaining_indices = np.delete(remaining_indices, query_indices)

        np.savetxt("C:\Data\Daten\Testdaten\LUT/x_train.txt", X_initial, delimiter="\t")
        np.savetxt("C:\Data\Daten\Testdaten\LUT/y_train.txt", y_initial, delimiter="\t")
        np.savetxt("C:\Data\Daten\Testdaten\LUT/x_test.txt", X_val, delimiter="\t")
        np.savetxt("C:\Data\Daten\Testdaten\LUT/training_indices_AL.txt", al_training_indices, delimiter="\t")

        yield {'type': 'result', 'model': model, 'al_training_indices': al_training_indices, 'performances': performances,
               'X_val': X_val, 'y_val': y_val, 'final_X': X_initial, 'final_y': y_initial}


class ProcessorTraining:

    def __init__(self, main):
        self.m = main
        # these are the four PROSAIL parameters to be estimated. Mind the order!
        # self.para_list = ['LAI', 'LIDF', 'cab', 'cm']
        self.para_list = []
        self.noisetype = 1
        self.sigma = 4
        self.mlra = None
        self.ml_params = {}
        self.al_training_indices, self.performances = (None, None)

        self.all_results_dict = {}
        self.best_hyperparameters_dict = {}
        self.best_score_dict = {}
        self.y_val_dict = {}

    def training_setup(self, lut_metafile, exclude_bands, npca, model_meta, para_list, noisetype=1, noiselevel=4,
                       algorithm='ANN', model_proc_dict=None,
                       use_al=False, use_insitu=False, n_initial=2,
                       perf_eval=False, split_method='train_test_split', kfolds=5, test_size=0.2, hyperp_tuning=False,
                       hyperparas_dict=None, query_strat='PAL', saveALselection=False, eval_on_insitu=False,
                       val_data=None,
                       soil_wavelengths=None, soil_specs=None):
        # Setup everything for training new models
        self.exclude_bands = exclude_bands  # the bands to be excluded for the training (water vapor absorption etc.)
        self.para_list = para_list

        # Add/multiply a noise term to LUT-spectra to gain more resilience towards real "noisy" spectra
        self.noisetype = noisetype  # 0: Off, 1: Gaussian, 2: Additive, 3: Multiplicative
        self.sigma = noiselevel  # std. of the noise in %

        # Algorithm/Training/AL Setup
        self.algorithm = algorithm  # name of the Algorithm ('ANN' by default)
        self.use_al = use_al
        self.use_insitu = use_insitu
        self.n_initial = n_initial

        self.perf_eval = perf_eval
        self.split_method = split_method
        self.kfolds = kfolds
        self.test_size = test_size

        self.hyperp_tuning = hyperp_tuning
        self.hyperparas_dict = hyperparas_dict
        self.query_strat = query_strat
        self.saveALselection = saveALselection
        self.eval_on_insitu = eval_on_insitu
        self.val_data = val_data

        self.soil_wavelengths = soil_wavelengths
        self.soil_specs = soil_specs

        self.n_jobs = os.cpu_count() // 2

        # LUT
        self.get_meta_LUT(lut_metafile=lut_metafile)  # read meta information of the LUT to be trained
        self.splits = int(self.meta_dict['splits'])  # number of splits per geo-ensemble in the LUT
        self.conversion_factor = int(self.meta_dict['multiplication_factor'])  # LUT boost e.g. 10000 for EnMAP
        self.lut_metafile = lut_metafile  # full path to the LUT metafile
        self.lut_basedir = os.path.dirname(lut_metafile)  # basic directory in which the LUT is stored
        self.lut_base = self.lut_basedir + "/" + str(self.meta_dict['name'])  # base name of the LUT

        # Retrain case: .proc file contains Scaler/PCA specifications and training indices
        self.model_proc_dict = model_proc_dict

        # Algorithm Output
        self.model_metafile = model_meta  # full path to the model metafile to be written (.meta)
        self.model_basedir = os.path.dirname(model_meta)  # basic directory in which the models are to be written
        self.model_name = os.path.splitext(os.path.basename(model_meta))[0]  # Name of the model = name of meta-file
        self.model_base = self.model_basedir + "/" + self.model_name  # base name of the model

        # Geo-ensembles are specified in the LUT meta file, create as lists
        self.tts = [float(i) for i in self.meta_dict['tts'] if i]
        self.tto = [float(i) for i in self.meta_dict['tto'] if i]
        self.psi = [float(i) for i in self.meta_dict['psi'] if i]

        self.ntts = len(self.tts)
        self.ntto = len(self.tto)
        self.npsi = len(self.psi)

        # npara_in_lut is NOT a list of the actually used parameters in PROSAIL for the LUT, but a list of all possible
        # parameters, since they are all present in the LUT even if they are not used
        self.npara_in_lut = len(self.meta_dict['parameters'])

        # inspecting one LUT-entry, the structure is always: first the parameter values then the reflectances
        # subset_bands_lut skips "npara_in_lut" values and jumps into reflectances, but also skips exclude_bands
        self.subset_bands_lut = [i + self.npara_in_lut for i in range(len(self.meta_dict['wavelengths']))
                                 if i not in self.exclude_bands]

        # # Training Values

        # Boosting the parameters may be necessary for some algorithms which cannot handle very small or large values
        # for the training (e.g. ANN fails when learning y=0.004, so it is boosted to y=4 according to "Functions.conv"
        self.para_boost = False

        # Which scaler should be used?
        # self.scaler = StandardScaler()  # create instance of standard scaler
        if not self.model_proc_dict:
            self.scaler = StandardScaler()
        else:
            self.scaler = self.model_proc_dict['scaler']
        if self.model_proc_dict:
            if 'pca' in self.model_proc_dict:
                self.pca = self.model_proc_dict['pca']
            else:
                self.pca = None
        elif npca > 0:
            self.pca = PCA(npca, random_state=42)  # create an instance of the PCA for the desired number of components
        else:
            self.pca = None

        self.components = npca  # how many components for the PCA? (0 if deactivated)

    def train_and_dump(self, prgbar_widget=None, qgis_app=None):
        # Train a model and dump the trained model to a file in the model directory
        # Number of models to be trained and dumped: one model per geo-ensemble and parameter
        nmodels_total = self.npsi * self.ntto * self.ntts * len(self.para_list)
        al_training_indices = None

        # Train Model for each geo-ensemble
        for rAA in range(self.npsi):
            for OZA in range(self.ntto):
                for SZA in range(self.ntts):

                    # number of geo-ensemble, corresponds to name of the LUT-file
                    geo_ensemble = rAA * self.ntto * self.ntts + OZA * self.ntts + SZA
                    X, y, lut = self.read_lut(
                        geo=geo_ensemble)  # read reflectances (X) and PROSAIL parameters (y) from LUT

                    # if self.use_al:
                    #     self.X_raw = np.copy(X)
                    if self.soil_specs:
                        subset_bands = [i for i in range(len(self.soil_wavelengths))
                                        if i not in self.exclude_bands]
                        soilspecs = [self.soil_specs[i] for i in subset_bands]
                        soilspecs = np.asarray(soilspecs).T
                        X = np.vstack((X, soilspecs))
                        add_zero_len = len(soilspecs)
                        zeroes = np.zeros((add_zero_len, y.shape[1]))
                        y = np.vstack((y, zeroes))

                    if self.noisetype > 0:
                        X = self._add_noise(ref_list=X, noisetype=self.noisetype, sigma=self.sigma,
                                            conversion=self.conversion_factor)

                    # Train and dump individual model per parameter
                    for ipara, para in enumerate(self.para_list):

                        model_no = geo_ensemble * len(self.para_list) + ipara + 1  # serial number of model

                        if self.use_al and not self.use_insitu:
                            prg_al_string = 'internal AL'
                        elif self.use_al and self.use_insitu:
                            prg_al_string = 'insitu AL'
                        elif self.hyperp_tuning:
                            prg_al_string = 'hyperparams tuned'
                        elif self.model_proc_dict:
                            prg_al_string = "RETRAIN"
                        else:
                            prg_al_string = 'non AL'

                        if self.hyperparas_dict:
                            hyperparams = self.hyperparas_dict
                        else:
                            hyperparams = {}

                        if self.scaler and not self.model_proc_dict:  # if X (reflectances) are to be scaled
                            self.scaler.fit(X)  # fit scaler
                            x = self.scaler.transform(X)

                        elif self.model_proc_dict:
                            x = self.scaler.transform(X)  # transform scaler
                        else:
                            x = np.copy(X)  # consecutive code needs x instead of X; copy if no scaler is used

                        # fit and transform a PCA
                        if self.pca and not self.model_proc_dict:
                            self.pca.fit(x)  # , y[:, ipara])
                            x = self.pca.transform(x)
                        elif self.model_proc_dict:
                            x = self.pca.transform(x)

                        if self.soil_specs:
                            soils_x = x[-len(soilspecs):, :]
                            soils_y = y[-len(soilspecs):, :]

                        if self.model_proc_dict:
                            # retraining case -> proc_dict carries training indices of previously
                            # trained AL model
                            if not self.eval_on_insitu:
                                self.X_val = squeeze_first_dim(x[self.model_proc_dict['test_indices']])
                                self.y_val = squeeze_first_dim(y[self.model_proc_dict['test_indices']])
                                x = squeeze_first_dim(x[self.model_proc_dict['split_training_indices']])
                                y = squeeze_first_dim(y[self.model_proc_dict['split_training_indices']])
                            x = squeeze_first_dim(x[self.model_proc_dict['al_training_indices']])
                            y = squeeze_first_dim(y[self.model_proc_dict['al_training_indices']])

                        if self.soil_specs:
                            x = np.vstack((x, soils_x))
                            y = np.vstack((y, soils_y))


                        if self.val_data:
                            self.insitu_data_setup(self.val_data)

                        self.init_model(var=para,
                                        hyperparams=hyperparams)  # initialize the model with the given settings

                        # Update progress bar
                        if prgbar_widget:
                            if prgbar_widget.gui.lblCancel.text() == "-1":
                                prgbar_widget.gui.lblCancel.setText("1")
                                prgbar_widget.gui.cmdCancel.setDisabled(False)
                                raise ValueError("Training cancelled!")

                            prgbar_widget.gui.lblCaption_r.setText(
                                'Training {} {} model {:d} of {:d}: {}'.format(
                                    prg_al_string, self.algorithm, model_no, nmodels_total, para))
                            qgis_app.processEvents()
                        else:
                            print("Training {} {} Noise {:d}-{:d} | {} | Geo {:d} of {:d}".format(prg_al_string,
                                                                                                  self.algorithm,
                                                                                                  self.noisetype,
                                                                                                  self.sigma, para,
                                                                                                  geo_ensemble + 1,
                                                                                                  self.ntts * self.ntto * self.npsi))

                        if self.perf_eval:  # performance evaluation
                            # result_dict is of type key 'result', 'progress', or 'hyperparameters'
                            al_training_indices = []
                            split_training_indices = []
                            test_indices = []
                            for result_dict in self.ml_model(
                                    X=x, y=y[:, ipara], model=self.mlra, **self.al_paras):
                                if result_dict["type"] == "result":  # results are ready, populate results
                                    model = result_dict["model"]
                                    # temp_dict = {}
                                    self.X_val = result_dict["X_val"]
                                    self.y_val = result_dict["y_val"]
                                    performances = np.array(result_dict["performances"])
                                    if self.use_insitu and self.algorithm == 'GPR':
                                        predictions, stds = model.predict(self.X_val, return_std=True)
                                        result_dict['stds'] = stds
                                    elif self.use_insitu and self.algorithm != 'GPR':
                                        predictions = model.predict(self.X_val)
                                    else:
                                        predictions = np.array(result_dict["predictions"])

                                    # if self.para_boost:
                                    #     # bring results back to original scale; #deprecated!
                                    #     self.y_val = self.y_val / self.m.func.conv[para][2]
                                    #     performances = performances / self.m.func.conv[para][2]
                                    #     predictions = predictions / self.m.func.conv[para][2]

                                    temp_dict = {
                                        "X_val": self.X_val,
                                        "y_val": self.y_val,
                                        "performances": performances,
                                        "predictions": predictions}
                                    # GPR yields prediciton stds, others not
                                    if 'stds' in result_dict:
                                        stds = np.array(result_dict['stds'])
                                        # if self.para_boost:
                                        #     stds = stds / self.m.func.conv[para][2]
                                        temp_dict['stds'] = stds
                                    if self.use_al:
                                        al_training_indices = result_dict["al_training_indices"]
                                        split_training_indices = result_dict["split_training_indices"]
                                        test_indices = result_dict["test_indices"]
                                    temp_dict["al_training_indices"] = al_training_indices
                                    temp_dict["split_training_indices"] = split_training_indices
                                    temp_dict["test_indices"] = test_indices
                                    self.all_results_dict[f'{para} {prg_al_string} {self.algorithm}'] = temp_dict

                                elif result_dict["type"] == "hyperparameters":
                                    if self.algorithm not in self.best_hyperparameters_dict:
                                        self.best_hyperparameters_dict[self.algorithm] = {}
                                    if self.algorithm not in self.best_score_dict:
                                        self.best_score_dict[self.algorithm] = {}

                                    self.best_hyperparameters_dict[self.algorithm][para] = {
                                        'hyperparas': result_dict["best_hyperparams"]}
                                    self.best_score_dict[self.algorithm][para] = {
                                        'best_score': result_dict["best_score"]}
                                    # print(self.best_hyperparameters_dict)
                                    # print(self.best_score_dict)

                                elif result_dict["type"] == "progress":  # progressbar updates

                                    progress = result_dict['progress']
                                    # loop_counter = result_dict['loop_counter']
                                    if prgbar_widget:
                                        prgbar_widget.gui.prgBar.setValue(int(progress))
                                        qgis_app.processEvents()
                                    else:
                                        print('Progress: {:d}%'.format(int(progress)))

                            if isinstance(performances,
                                          list):  # weird exception handling to get rid of potential sublists
                                for element in performances:
                                    if isinstance(element, list):
                                        if len(performances[0]) == 1:
                                            performances = np.asarray(performances).reshape((1, 1))

                        else:  # no performance evaluation means just fitting the model without feedback
                            model = self.ml_model(X=x, y=y[:, ipara], model=self.mlra)

                        if not self.use_al and len(self.para_list) > 1:
                            prgbar_widget.gui.prgBar.setMaximum(100)
                            prgbar_widget.gui.prgBar.setValue(int(model_no / nmodels_total * 100))
                            qgis_app.processEvents()

                        # The final trained model is saved
                        joblib.dump(model, self.model_base + "_{:d}_{}{}".format(geo_ensemble,
                                                                                 para,
                                                                                 self.ml_model_ext))  # dump (save) model to file for later use

                        # save the AL selection LUT if Checkbox is checked.
                        if self.saveALselection and al_training_indices:
                            out_name = self.model_name + "_{}_AL_selection".format(para)
                            out_lut = np.squeeze(lut[:, al_training_indices])
                            np.save(self.model_basedir + '/' + out_name + '_0_0', out_lut)
                            with open("%s_00meta.lut" % (self.model_basedir + '/' + out_name), "w") as meta:
                                meta.write("name=%s" % out_name)
                                meta.write("\nn_total=%i" % (np.shape(lut[:, al_training_indices])[-1]))
                                meta.write("\nparameters={}".format(para))
                                meta.write("\nsplits=%i" % 1)
                                meta.write("\ntts={}".format(";".join(i for i in self.meta_dict['tts'])))
                                meta.write("\ntto={}".format(";".join(i for i in self.meta_dict['tto'])))
                                meta.write("\npsi={}".format(";".join(i for i in self.meta_dict['psi'])))
                                meta.write("\nmultiplication_factor=%i" % int(self.meta_dict['multiplication_factor']))
                                meta.write(
                                    "\nwavelengths={}".format(";".join(str(i) for i in self.meta_dict['wavelengths'])))

        # Not Done yet! Save further information to the base-folder: information about scaler and pca
        # are saved to a .proc-file; this file is read before calling predict on a model to prepare spectral data
        # the same way as the LUT-spectra were preprocessed in this routine; there is one .proc-file per parameter,
        # since scaler and pca can/does vary between parameters; however: at the time being, scaler and PCA are the
        # same for all parameters and are saved as copies
        if al_training_indices:
            for para in self.para_list:
                processing_dict = {"scaler": self.scaler, "pca": self.pca, "al_training_indices": al_training_indices,
                                   "split_training_indices": split_training_indices, "test_indices": test_indices}
                joblib.dump(processing_dict, self.model_base + '_{}.proc'.format(para))  # dump the .proc-file as well
        else:
            for para in self.para_list:
                processing_dict = {"scaler": self.scaler, "pca": self.pca, "test_indices": test_indices}
                joblib.dump(processing_dict, self.model_base + '_{}.proc'.format(para))  # dump the .proc-file as well

        # Write Model Meta
        with open(self.model_metafile, 'w') as para_file:  # Meta-information; one meta-file for all paras!
            para_file.write("alg={}\nnoisetype={:d}\nnoiselvl={:d}%\nPCA_components={:d}\nscaler={}"
                            .format(self.algorithm, self.noisetype, self.sigma, self.components, str(self.scaler)))
            para_file.write("\ntarget_parameters=" + ";".join(str(i) for i in self.para_list))
            para_file.write("\ntts=" + ";".join(str(i) for i in self.tts))
            para_file.write("\ntto=" + ";".join(str(i) for i in self.tto))
            para_file.write("\npsi=" + ";".join(str(i) for i in self.psi))
            para_file.write("\nexclude_bands=" + ";".join(str(i) for i in self.exclude_bands))
            if self.use_al:
                para_file.write("\nactive_learning=" + str(self.use_al))
            if self.hyperp_tuning:
                para_file.write("\nbest_hyperparameters=" + str(
                    self.best_hyperparameters_dict[self.algorithm]))
                para_file.write("\nbest_score=" + str(self.best_score_dict[self.algorithm]))

        # write found hyperparameters
        if self.hyperp_tuning:
            # print(self.best_hyperparameters_dict)
            joblib.dump(self.best_hyperparameters_dict,
                        self.model_base + '.hyper')

    def insitu_data_setup(self, val_data):
        # Scaling and PCA dim reduction of insitu spectra
        self.y_val_dict = {key: val_data[key] for key in val_data if key not in ['Reflectance', 'Wavelengths']}
        X_val = val_data.get('Reflectance')
        wavelengths = val_data.get('Wavelengths')

        subset_bands = [i for i in range(len(wavelengths))
                        if i not in self.exclude_bands]

        X_val = [X_val[i] for i in subset_bands]
        X_val = np.asarray(X_val).T

        if self.noisetype > 0:
            X_val = self._add_noise(ref_list=X_val, noisetype=self.noisetype, sigma=self.sigma,
                                    conversion=self.conversion_factor)

        if self.scaler:
            X_val = self.scaler.transform(X_val)  # transform scaler
        else:
            X_val = np.copy(X_val)

        if self.pca:
            self.X_val = self.pca.transform(X_val)
        else:
            self.X_val = X_val

    def validation_setup(self, val_file, exclude_bands, npca):
        # only for external usage via _exec.py direct execution test environment
        self.val_file = val_file
        val_data = np.loadtxt(self.val_file, delimiter="\t", skiprows=1)
        X_val = val_data[2:, 1:].T / 10000
        self.y_val = val_data[0, 1:]

        self.exclude_bands = exclude_bands  # the bands to be excluded for the training (water vapor absorption etc.)

        if self.scaler:  # if X (reflectances) are to be scaled
            self.scaler.fit(X_val)  # fit scaler
            X_val = self.scaler.transform(X_val)  # transform scaler
        else:
            X_val = np.copy(X_val)

        if npca > 0:
            self.pca = PCA(npca)  # create an instance of the PCA for the desired number of components
        else:
            self.pca = None

        if self.pca:
            self.pca.fit(X_val)  # , y[:, ipara])
            self.X_val = self.pca.transform(X_val)
    # for __main__ use only

    def init_model(self, var, hyperparams=None):
        # 1. Initialization with default settings
        self.ml_params = MLRA_defaults.__dict__[self.algorithm].get(
            var, MLRA_defaults.__dict__[self.algorithm]['default']).copy()
        # 2. Update with provided hyperparameters, if any
        if hyperparams and var in hyperparams[self.algorithm]:
            hyperparams_for_var = hyperparams[self.algorithm][var]['hyperparas']
            self.ml_params.update(hyperparams_for_var)

        # method to initialize a model, i.e. prepare an algorithm before it sees any data
        if self.algorithm == 'ANN':
            self.ml_model_ext = '.ann'  # extension of the models to recognize it as a neural network model
            self.mlra = MLPRegressor(**self.ml_params)

        elif self.algorithm == 'GPR':
            self.ml_model_ext = '.gpr'
            self.mlra = GaussianProcessRegressor(**self.ml_params)

        elif self.algorithm == 'RFR':
            self.ml_model_ext = '.rfr'  # extension for RFR model
            self.mlra = RandomForestRegressor(**self.ml_params)

        elif self.algorithm == 'SVR':
            self.ml_model_ext = '.svr'
            self.mlra = SVR(**self.ml_params)

        elif self.algorithm == 'KRR':
            self.ml_model_ext = '.krr'  # extension of the models to recognize it as a KRR model
            self.mlra = KernelRidge(**self.ml_params)

        elif self.algorithm == 'GBR':
            self.ml_model_ext = '.gbr'  # extension of the models to recognize it as a GBR model
            self.mlra = GradientBoostingRegressor(**self.ml_params)

        if self.hyperp_tuning:
            param_dist = MLRA_defaults.__dict__[self.algorithm]['param_dist']
            # TODO: add radiobutton for tuning options
            self.mlra = self.init_hyperparameter_tuning(self.mlra, param_dist, mode='randomized', n_jobs=self.n_jobs)

        # AL based on split (train-test-split or kfold cross val)
        if self.use_al and not self.use_insitu:
            self.al_paras = {'split_method': self.split_method, 'kfolds': self.kfolds,
                             'test_size': self.test_size,
                             'init_percentage': self.n_initial, 'query_strat': self.query_strat, 'n_jobs': self.n_jobs}
            self.ml_model = self.m.mlra_training._al_loop_internal

        # AL with external insitu data
        elif self.use_al and self.use_insitu:
            if self.y_val_dict:
                self.y_val = np.asarray(self.y_val_dict.get(var))

            self.al_paras = {'X_val': self.X_val, 'y_val': self.y_val,
                             'init_percentage': self.n_initial, 'query_strat': self.query_strat, 'n_jobs': self.n_jobs}
            self.ml_model = self.m.mlra_training._al_loop

        # No AL, training on splits
        elif (not self.use_al and self.perf_eval and not self.hyperp_tuning and not self.eval_on_insitu
              and not self.model_proc_dict):
            self.al_paras = {'split_method': self.split_method, 'kfolds': self.kfolds, 'test_size': self.test_size}
            self.ml_model = self.m.mlra_training._fit_split
        # No AL, Training on full Training data with evaluation on insitu data
        # -> The Retraining case
        elif self.eval_on_insitu and not self.hyperp_tuning:
            if self.y_val_dict:
                self.y_val = np.asarray(self.y_val_dict.get(var))
            self.al_paras = {'X_val': self.X_val, 'y_val': self.y_val}
            self.ml_model = self.m.mlra_training._fit_insitu_or_testset
        # No AL, Training on full Training data with evaluation on previous test data split
        # -> The internal Retraining case
        elif not self.eval_on_insitu and self.model_proc_dict:
            self.al_paras = {'X_val': self.X_val, 'y_val': self.y_val}
            self.ml_model = self.m.mlra_training._fit_insitu_or_testset
        # No AL, training with hyperparameter tuning
        elif self.hyperp_tuning:
            if self.eval_on_insitu:
                self.y_val = np.asarray(self.y_val_dict.get(var))
                self.al_paras = {'test_size': self.test_size, 'X_val': self.X_val, 'y_val': self.y_val}
            else:
                self.al_paras = {'test_size': self.test_size}
            self.ml_model = self.m.mlra_training._fit_hyper
        # No AL, only training -> all samples
        else:
            self.ml_model = self.m.mlra_training._fit  # construct the model and pass it to self.ml_model

    def init_hyperparameter_tuning(self, mlra, param_dist, mode, n_iter_search=10, n_jobs=1):
        scoring = 'neg_root_mean_squared_error'
        if mode == 'randomized':
            search = RandomizedSearchCV(mlra, param_distributions=param_dist, n_iter=n_iter_search,
                                        n_jobs=n_jobs,
                                        verbose=4, scoring=scoring)
        elif mode == 'grid':
            search = GridSearchCV(mlra, param_grid=param_dist,
                                  n_jobs=n_jobs,
                                  verbose=4, scoring=scoring)
        else:
            raise ValueError(f"Mode {mode} not recognized!")

        return search

    def get_result_dict(self):
        return self.all_results_dict

    def get_hyperparams_dict(self):
        return self.best_hyperparameters_dict

    def get_meta_LUT(self, lut_metafile):
        # opens the LUT-metafile and processes the content
        with open(lut_metafile, 'r') as meta_file:
            content = meta_file.readlines()
            content = [item.rstrip("\n") for item in content]

        # Super fancy! This splits the keys and values in the LUT and extracts the values separated by ";"
        keys, values = list(), list()
        [[x.append(y) for x, y in zip([keys, values], line.split(sep="=", maxsplit=1))] for line in content]
        values = [value.split(';') if ';' in value else value for value in values]
        self.meta_dict = dict(zip(keys, values))  # dictionary for meta-information in the LUT
        # dictionary for the parameters stored in the LUT
        # ['N', 'cab', 'car', 'anth', 'cbrown', 'cw', 'cm', 'cp', 'cbc', 'LAI', 'typeLIDF', 'LIDF', 'hspot', 'psoil', 'tts', 'tto', 'psi', 'LAIu', 'cd', 'sd', 'h']
        self.para_dict = dict(zip(self.meta_dict['parameters'], list(range(len(self.meta_dict['parameters'])))))
        for geo in ['tts', 'tto', 'psi']:  # happens when only one angle is provided (no ";"-split)
            if not isinstance(self.meta_dict[geo], list):  # reads as: if meta_dict[geo] is not of type "list"
                self.meta_dict[geo] = [self.meta_dict[geo]]  # then make it one!

    def read_lut(self, geo):
        # open a lut-file and reads the content; loads all splits of one geo-ensemble which is passed into the method
        lut = np.hstack([np.load(self.lut_base + '_{:d}_{:d}'.format(geo, split) + ".npy")
                         for split in range(self.splits)])  # load all splits of the current geo_ensembles
        # only select the rows with correct band information, then transpose into columns
        X = np.asarray(lut[self.subset_bands_lut, :]).T

        y = np.zeros(shape=(lut.shape[1], len(self.para_list)))  # open up a new array for PROSAIL parameters

        #  all LUT_params
        #  ['N', 'cab', 'car', 'anth', 'cbrown', 'cw', 'cm', 'cp', 'cbc', 'LAI', 'typeLIDF', 'LIDF', 'hspot', 'psoil', 'tts', 'tto', 'psi', 'LAIu', 'cd', 'sd', 'h']
        for i, para in enumerate(self.para_list):  # extract parameters
            # check if para is *'derived' and calculate:
            if para == 'AGBdry':
                y[:, i] = (lut[self.para_dict['cp'], :]
                           + lut[self.para_dict['cbc'], :]) * lut[self.para_dict['LAI'], :] * 10000
            if para == 'AGBfresh':
                y[:, i] = (lut[self.para_dict['cp'], :] + lut[self.para_dict['cbc'], :]
                           + lut[self.para_dict['cw'], :]) * lut[self.para_dict['LAI'], :] * 10000
            if para == 'CWC':
                y[:, i] = lut[self.para_dict['cw'], :] * lut[self.para_dict['LAI'], :]
            if para == 'Nitrogen':
                y[:, i] = (lut[self.para_dict['LAI'], :] * lut[self.para_dict['cp'], :] * 10000) / 4.43
            if para == 'Carbon':
                y[:, i] = (lut[self.para_dict['LAI'], :] * lut[self.para_dict['cbc'], :] * 10000) / 2.31

            if para in self.para_dict:
                y[:, i] = lut[self.para_dict[para], :]

            if self.para_boost:  # and para in self.para_dict:  # to boost or not to boost
                y[:, i] = y[:, i] * self.m.func.conv.get(para)[2]

        return X, y, lut

    def _add_noise(self, ref_list, noisetype, sigma, conversion):
        # noise module to put a noise term on top of PROSAIL spectra

        # sigma (strength of the noise) is provided as %, so it needs to be converted to relative values
        # and optionally multiplied with the conversion factor to match reflectance value ranges for additive noise
        if noisetype == 0:  # no noise
            return ref_list
        elif noisetype == 1:  # gaussian noise
            noise_std = np.std(ref_list) * sigma / 100
            ref_noisy = self.m.func.get_random_normal(loc=0.0, scale=noise_std, size=ref_list.shape) + ref_list
        elif noisetype == 2:  # additive noise
            sigma_c = (sigma / 100) * conversion  # sigma converted (e.g. 0...1 -> 0...10000)
            ref_noisy = self.m.func.get_random_normal(loc=0.0, scale=sigma_c, size=ref_list.shape) + ref_list
        elif noisetype == 3:  # multiplicative noise
            ref_noisy = (1 + self.m.func.get_random_normal(loc=0.0, scale=sigma / 100, size=ref_list.shape)) * ref_list
        else:
            return None
        ref_noisy[ref_noisy < 0] = 0  # stochastic process may happen to produce ref < 0 -> set to zero
        return ref_noisy


# Class to handle predicting variables from spectral reflectances with pre-trained Machine Learning (ML) algorithms
# At the moment, only ANNs are implemented, but potentially this script could be appended by any other ML-algo
class ProcessorPrediction:
    def __init__(self, main):
        self.m = main

        # Some basic information about the algorithm; svr is added just for the sake of demonstration
        self.mlra_meta = {'ANN': {'name': 'ann', 'file_ext': '.ann', 'file_name': 'ann_mlp'},
                          'GPR': {'name': 'gpr', 'file_ext': '.gpr', 'file_name': 'gpr_mlp'},
                          'RFR': {'name': 'rfr', 'file_ext': '.rfr', 'file_name': 'rfr_mlp'},
                          'SVR': {'name': 'svr', 'file_ext': '.svr', 'file_name': 'svr_mlp'},
                          'KRR': {'name': 'krr', 'file_ext': '.krr', 'file_name': 'krr_mlp'},
                          'GBR': {'name': 'gbr', 'file_ext': '.gbr', 'file_name': 'gbr_mlp'}}

    def prediction_setup(self, model_meta, img_in, res_out, out_mode, mask_ndvi, ndvi_thr, ndvi_bands, mask_image,
                         geo_in, spatial_geo, paras, algorithm, gpr_flag, fixed_geos=None, nodat=None):
        # Setting up everything for the prediction

        self.model_meta = model_meta
        self.model_dir = os.path.dirname(model_meta)  # directory in which the models are stored
        self.model_name = os.path.splitext(os.path.basename(model_meta))[0]  # base-name of the model

        self.img_in = img_in  # Input Image to be inverted
        self.res_out = res_out  # File for output results
        self.out_mode = out_mode  # "single" file or "individual" files as output
        self.mask_ndvi = mask_ndvi  # True: Do mask NDVI < threshold; False: Do not mask
        self.ndvi_thr = ndvi_thr  # Threshold above which a pixel is inverted if mask_ndvi == True
        self.ndvi_bands = ndvi_bands  # which bands are used to calculate the NDVI?
        self.mask_image = mask_image  # Image with 0 and 1 to set masked areas
        self.geo_in = geo_in  # Image file with geometry (SZA, OZA, rAA)
        # should each pixel be inverted according to its geometry (True) or calculate the average for all pixels (False)
        self.spatial_geo = spatial_geo
        self.paras = paras  # Which PROSAIL parameters should be estimated? LAI, ALIA, cab, cm
        self.algorithm = algorithm
        self.gpr_flag = gpr_flag
        if self.gpr_flag is True:
            self.res_out_std = str(os.path.splitext(self.res_out)[0] + '_std' + os.path.splitext(self.res_out)[1])

        if fixed_geos is None:  # no fixed geo for the image
            self.tts_unique, self.tto_unique, self.psi_unique = [None, None, None]
        else:  # one geometry value for the whole image
            self.tts_unique, self.tto_unique, self.psi_unique = fixed_geos
        if nodat is None:
            self.nodat = [-9999, -9999, -9999]
        else:
            self.nodat = [nodat] * 3

    def predict_from_dump(self, prg_widget=None, qgis_app=None):
        # Load the trained ML-algorithms which were dumped by "train and dump" and estimate PROSAIL parameters with them
        if prg_widget:
            prg_widget.gui.lblCaption_r.setText('Reading Input Image...')
            qgis_app.processEvents()

        # Read the spectral image
        nrows, ncols, nbands, self.grid, in_matrix = self.m.func._read_image(image=self.img_in, dtype=np.float32)

        # Inspect the ML meta file (.meta) and find out which geo-ensembles were trained
        with open(self.model_meta, 'r') as mlra_metafile:
            metacontent = mlra_metafile.readlines()
            metacontent = [line.rstrip('\n') for line in metacontent]
        self.all_tts = [float(i) for i in metacontent[6].split("=")[1].split(";")]
        self.all_tto = [float(i) for i in metacontent[7].split("=")[1].split(";")]
        self.all_psi = [float(i) for i in metacontent[8].split("=")[1].split(";")]
        try:
            self.exclude_bands = [int(i) for i in metacontent[9].split("=")[1].split(";")]
        except:
            self.exclude_bands = []

        if prg_widget:
            prg_widget.gui.lblCaption_r.setText('Reading Geometry...')
            qgis_app.processEvents()

        # SZA, OZA, rAA: angles * 100 (e.g. SZA 4500 = 45°)
        if self.geo_in:  # A file is given by the user, which consists of 3 bands (SZA, OZA, rAA)
            geometry_matrix = self.m.func.read_geometry(geo_in=self.geo_in)  # read the geometry file
            if not self.spatial_geo:
                # get rid of spatial distribution of geometry (tts, tto, psi) within image
                # Place the spatial mean everywhere and nevermind the nans
                geometry_matrix[geometry_matrix == self.nodat[1]] = np.nan
                geometry_matrix[0, :, :] = np.nanmean(geometry_matrix[0, :, :])
                geometry_matrix[1, :, :] = np.nanmean(geometry_matrix[1, :, :])
                geometry_matrix[2, :, :] = np.nanmean(geometry_matrix[2, :, :])
        else:
            # no Geometry-file, so the user needs to fix the three angles
            # Build the geometry-matrix from scratch
            geometry_matrix = np.zeros(shape=(3, nrows, ncols))
            geometry_matrix[0, :, :] = self.tts_unique * 100  # geometry boost is always 100
            geometry_matrix[1, :, :] = self.tto_unique * 100
            geometry_matrix[2, :, :] = self.psi_unique * 100

        if self.mask_image:
            # if a mask_image is supplied, read it and save the boolean mask to self.mask
            if prg_widget:
                prg_widget.gui.lblCaption_r.setText('Reading Mask Image...')
                qgis_app.processEvents()
            _, _, _, _, self.mask = self.m.func._read_image(image=self.mask_image, dtype=np.int8)

        if self.mask_ndvi:
            # If the user wants to mask pixels with NDVI below the Threshold: calculate another mask from ndvi
            if prg_widget:
                prg_widget.gui.lblCaption_r.setText('Applying NDVI Threshold...')
                qgis_app.processEvents()

            # Get the RED and NIR-band for NDVI calculation; at this point, the in_matrix is still with all the bands,
            # because "self.ndvi_bands" applies to full spectrum with no bands ignored
            self.ndvi_mask = self.m.func._ndvi(bands=self.ndvi_bands, in_matrix=in_matrix,
                                               thr=self.ndvi_thr)

        # whichModel is equivalent to "whichLUT"; each model has a certain "ID" so that it can be related to one
        # geo-ensemble; the script needs to find out, which "whichModel" applies at which pixel
        whichModel = self.m.func._which_model(geometry_matrix=geometry_matrix,
                                              geo=(self.all_tts, self.all_tto, self.all_psi))

        # find out, which "whichModels" are actually found in the geo_image
        self.whichModel_unique = np.unique(whichModel)
        whichModel_coords = list()

        # Working with masks to find out, which pixels need to be inverted. First set the mask to shape and all == True
        all_true = np.full(shape=(nrows, ncols), fill_value=True)

        # Find out coordinates for which ALL constraints hold True in each "whichModel"
        # The result is a "map" in which each pixel stores the ID of the model to be used (depending on geometry)
        for iwhichModel in self.whichModel_unique:  # Mask depending on constraints
            whichModel_coords.append(np.where((whichModel[:, :] == iwhichModel) &  # present Model
                                              (self.mask[0, :, :] > 0 if self.mask_image else all_true) &  # not masked
                                              (self.ndvi_mask > 0 if self.mask_ndvi else all_true) &  # NDVI masked
                                              (~np.all(in_matrix == self.nodat[0], axis=0))))  # not NoDatVal

        _, nrows, ncols = in_matrix.shape
        # Prepare output-matrix and will it with nodata
        self.out_matrix = np.full(shape=(len(self.paras), nrows, ncols), fill_value=self.nodat[2], dtype=np.float64)
        # self.predict does the actual prediction and returns a matrix that overwrites self.out_matrix
        # it seems confusing to prepare a matrix and then overwrite it, but self.predict needs self.out_matrix
        # as an argument!
        self.out_matrix, self.out_matrix_std = self.predict(image=in_matrix, whichModel_coords=whichModel_coords, out_matrix=self.out_matrix,
                                       prg_widget=prg_widget, qgis_app=qgis_app)

    def write_prediction(self):
        # Write the estimated parameters to file
        self.m.func.write_image(out_matrix=self.out_matrix, image_out=self.res_out, grid=self.grid,
                                out_mode=self.out_mode, nodat=self.nodat[2], paras_out=self.paras)

    def write_prediction_std(self):
        # Write the estimated parameters to file
        self.m.func.write_image(out_matrix=self.out_matrix_std, image_out=self.res_out_std, grid=self.grid,
                                out_mode=self.out_mode, nodat=self.nodat[2], paras_out=self.paras)

    def predict(self, image, whichModel_coords, out_matrix, prg_widget, qgis_app):
        # Delete the bands to be excluded (they were stored in the ML-metafile) so that it matches with how the
        # models were trained (during training, exclude_bands were ignored in the LUT)
        image = np.delete(image, self.exclude_bands, axis=0)
        nbands, nrows, ncols = image.shape  # update image shape

        # In Sklearn, prediction of multiple data inputs at once is possible, but not as a 2D-array
        # We need to "collapse" the second dimension and create one long dim as follows:
        image = image.reshape((nbands, -1))  # collapse rows and cols into 1 dimension
        image = np.swapaxes(image, 0, 1)  # place predictors into the right position (where sklearn expects them)

        out_matrix_std = None

        # Do this for each PROSAIL parameter after another
        for ipara, para in enumerate(self.paras):
            if prg_widget:
                prg_widget.gui.lblCaption_r.setText('Predicting {} (parameter {:d} of {:d})...'
                                                    .format(para, ipara + 1, len(self.paras)))
                qgis_app.processEvents()

            # Load the right model from drive; it's actually a .npz file, so the arrays of .proc can be
            # addressed like a dictionary; in the .proc-file the preprocession of the LUT is stored to perform
            # the same on the spectral image
            process_dict = joblib.load(self.model_dir + "/" + self.model_name + "_{}".format(para) + '.proc')
            # print(process_dict)

            # Make a copy of the input image and only work on that one to keep the original image.
            # This is memory expensive but better than loading image over and over again
            image_copy = np.copy(image).astype(dtype=np.float32)
            # print(image_copy.shape)

            # scale the reflectance data according to the scaler
            if process_dict['scaler']:
                image_copy = process_dict['scaler'].transform(image_copy)

            # perform a PCA on the reflectance data
            if process_dict['pca']:
                image_copy = process_dict['pca'].transform(image_copy)

            nbands_para = image_copy.shape[1]
            # Now put the image back into the old 3D-shape
            image_copy = image_copy.reshape((nrows, ncols, nbands_para))

            n_geo = len(self.all_tts) * len(self.all_tto) * len(self.all_psi)
            mod = list()

            # Browse through all geo-ensembles and add the models as objects to the mod-list
            for igeo in range(n_geo):
                mod.append(joblib.load(
                    self.model_dir + "/" + self.model_name + '_{:d}_{}'.format(igeo, para) + '.' + self.algorithm))

            # Browse through all models that were trained
            for i_imodel, imodel in enumerate(self.whichModel_unique):
                if whichModel_coords[i_imodel][0].size == 0:
                    continue  # after masking, not all 'imodels' are present in the image_copy

                if isinstance(mod[imodel], GaussianProcessRegressor):
                    result, result_std = mod[imodel].predict(image_copy[whichModel_coords[i_imodel][0],
                                                 whichModel_coords[i_imodel][1], :], return_std=True)
                    out_matrix_std = np.copy(out_matrix)
                    out_matrix_std[ipara, whichModel_coords[i_imodel][0], whichModel_coords[i_imodel][
                        1]] = result_std

                else:
                    # This is the core "predict" command in which the algorithm is asked to estimate from what it has learnt
                    result = mod[imodel].predict(image_copy[whichModel_coords[i_imodel][0],
                                             whichModel_coords[i_imodel][1], :])

                out_matrix[ipara, whichModel_coords[i_imodel][0], whichModel_coords[i_imodel][
                        1]] = result  # / self.m.func.conv[para][2]

                # Convert the results and put it into the right position
                # out_matrix[parameter, row, col], row and col is stored in the coordinates of whichModel

        return out_matrix, out_matrix_std


# Some basic functions are placed in this class
class Functions:
    def __init__(self, main):
        self.m = main

        # self.conv is a dictionary for additional information about paras
        # Convention: {"para": [full name, [ylim/xlim], boost]}
        # ylim/xlim is useful for plotting results
        # boost is used to boost the parameters into preferred ranges of e.g. 0..1 or 0..100 instead of 0..0.0001
        self.conv = {
            "N": ["N", [1.0, 2.2], 1],
            "cab": ["chlorophyll", [10, 80], 1],
            "cw": ["EWT_S", [0.001, 0.07], 1000],
            "cm": ["LMA", [0.0025, 0.006], 1000],
            "LAI": ["greenLAI", [0.0, 8.0], 1],
            "typeLIDF": ["typeLIDF", [1.0, 2.0], 1],
            "LIDF": ["ALIA_S", [10, 80], 1],
            "hspot": ["hspot", [0.0, 0.1], 100],
            "psoil": ["psoil", [0.0, 1.0], 10],
            "tts": ["tts"],
            "tto": ["tto"],
            "psi": ["psi"],
            "cp": ["cp", [0.0, 0.002], 1000],
            "cbc": ["ccl", [0.0, 0.005], 1000],
            "car": ["Car", [0.0, 20.0], 1],
            "anth": ["Canth", [0.0, 5.0], 1],
            "cbrown": ["brown_pigments", [0.0, 1.0], 10],
            "AGBdry": ["AGBdry", [0.0, 2000.0], 0.001],
            "AGBfresh": ["AGBfresh", [0.0, 5000.0], 0.001],
            "CWC": ["CWC", [0.0, 0.3], 1],
            "Nitrogen": ["Nitrogen", [0.0, 40], 0.1],
            "Carbon": ["Carbon", [0.0, 600], 0.001]
        }

    @staticmethod
    def _ndvi(bands, in_matrix, thr):
        # Calculates the NDVI when the two bands ([0]: red, [1]: nir) are supplied
        red, nir = bands[0], bands[1]
        ndvi_out = (in_matrix[nir, :, :] - in_matrix[red, :, :]) / (in_matrix[nir, :, :] + in_matrix[red, :, :])
        ndvi_out = np.nan_to_num(ndvi_out)
        ndvi_out = np.where(ndvi_out > thr, 1, 0)  # mask all ndvi values above a certain threshold (thr) with 0
        return ndvi_out

    @staticmethod
    def _read_image(image, dtype=np.float32):
        # Method for loading bsq images, no bands are skipped anymore
        dataset = openRasterDataset(image)
        in_matrix = dataset.readAsArray().astype(dtype=dtype)
        nbands, nrows, ncols = in_matrix.shape
        grid = dataset.grid()

        return nrows, ncols, nbands, grid, in_matrix  # return a tuple back to the last function (type "dtype")

    @staticmethod
    def write_image(out_matrix, image_out, grid, paras_out, nodat, out_mode):
        # Method for writing output to binary raster file
        if out_mode == 'single':  # write one single file with multiple bands
            output = RasterDataset.fromArray(array=out_matrix, filename=image_out, grid=grid,
                                             driver=EnviDriver())
            output.setMetadataItem('data ignore value', nodat, 'ENVI')

            for iband, band in enumerate(output.bands()):
                band.setDescription(paras_out[iband])
                band.setNoDataValue(nodat)

        else:  # write several files, one per parameters
            for ipara in range(len(paras_out)):
                # naming convention: drop extension, add para name, add extension
                base, ext = os.path.splitext(image_out)
                image_out_individual = base + "_" + paras_out[ipara] + ext
                output = RasterDataset.fromArray(array=out_matrix[ipara, :, :], filename=image_out_individual,
                                                 grid=grid, driver=EnviDriver())
                output.setMetadataItem('data ignore value', nodat, 'ENVI')
                band = next(output.bands())  # output.bands() is a generator; here only one band
                band.setDescription(paras_out[ipara])
                band.setNoDataValue(nodat)

    def read_geometry(self, geo_in):
        # Read geometry from input file (raster based)
        _, georows, geocols, _, geometry_raw = self._read_image(image=geo_in)

        # Detect data range by inspecting the mean SZA in the image (where SZA > 0)
        mean_sza = np.mean(geometry_raw[geometry_raw > 0])
        int_boost_geo = 10 ** (np.ceil(np.log10(mean_sza)) - 2)  # evaluates as 1 for SZA=45, 100 for SZA=4500, ...

        geometry_matrix = np.empty(shape=(3, georows, geocols))  # three "bands" for SZA, OZA, rAA
        geometry_matrix.fill(-9999)
        geometry_matrix = geometry_raw / int_boost_geo  # insert all geometries from file into the geometry matrix

        return geometry_matrix

    @staticmethod
    def _which_model(geometry_matrix, geo):
        nrows = geometry_matrix.shape[1]
        ncols = geometry_matrix.shape[2]
        tts, tto, psi = geo

        # whichLUT is an array with shape of the input image; the pixel values set an integer number which
        # identifies the LUT to be used. Notice that the same LUT is calculated for different geometry-constellations
        # and those constellations are numbered as integers according to what is specified in the .lut-meta-file
        whichModel = np.zeros(shape=(nrows, ncols), dtype=np.int16)

        for row in range(nrows):
            for col in range(ncols):
                # find the geometrical setting that is closest to the geometry that is actually observed
                # tts_LUT, tto_LUT and psi_LUT are the constellations present in the LUT
                angles = list()
                angles.append(np.argmin(np.abs(geometry_matrix[0, row, col] - tts)))  # tts
                angles.append(np.argmin(np.abs(geometry_matrix[1, row, col] - tto)))  # tto
                angles.append(np.argmin(np.abs(geometry_matrix[2, row, col] - psi)))  # psi

                # find out the number of the LUT to be used - they are sorted in the following order
                #  0    1    2   ...  5    6   ... ...  31   32   ... n_total   -> for case psin = 6, tton = 5
                # tts0 tts0 tts0 ... tts0 tts0 ... ... tts0 tts1  ...  ttsn     -> n = len(tts)
                # tto0 tto0 tto0 ... tto0 tto1 ... ... tton tto0  ...  tton     -> n = len(tto)
                # psi0 psi1 psi2 ... psin psi0 ... ... psin psi0  ...  psin     -> n = len(psi)
                whichModel[row, col] = angles[2] * len(tto) * len(tts) + angles[1] * len(tts) + angles[0]

        return whichModel

    @staticmethod
    def get_random_normal(loc, scale, size, random_state=42):
        rng = np.random.default_rng(random_state)
        return rng.normal(loc=loc, scale=scale, size=size)



class ProcessorMainFunction:
    def __init__(self):
        self.mlra_training = MLRATraining(self)
        self.func = Functions(self)
        self.predict_main = ProcessorPrediction(self)
        self.train_main = ProcessorTraining(self)
