# -*- coding: utf-8 -*-
"""
***************************************************************************
    Processor_Inversion_core.py - LMU Agri Apps - Artificial Neural Network based spectroscopic image inversion of
    PROSAIL parameters - CORE
    -----------------------------------------------------------------------
    begin                : 09/2020
    copyright            : (C) 2020 Martin Danner; Matthias Wocher
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

This script uses pre-trained Machine Learning (ML) algorithms to predict / estimate PROSAIL parameters
from spectral images. At the time being, the "processor" will only rely on Artificial Neural Networks
(Multi-Layer-Perceptron-Regression; MLPR), because they yield good results, are fast, take little memory and are
easier to handle than SVR or GPR. The basic idea is that algorithms are already distributed through the EnMAP-box,
but new algorithms can always be created manually by updating the values in this script. While this _core module
can do both training and prediction, the GUIs are split into different scripts.

"""
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)

from _classic.hubflow.core import *
import numpy as np
from PyQt5 import QtCore

from Processor_Training_MLRA_defaults import MLRA_defaults

from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.kernel_ridge import KernelRidge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import expon, reciprocal

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

from sklearn.metrics import pairwise_distances
from sklearn.model_selection import KFold, train_test_split
# from sklearn.linear_model import LinearRegression
from sklearn.model_selection import check_cv
from sklearn.model_selection import cross_val_predict
from sklearn.base import is_classifier


import matplotlib as mpl
import matplotlib.pyplot as plt
import joblib


def max_euclidean_distances(data1, data2, n):
    # Compute all pairwise distances
    all_distances = pairwise_distances(data1, data2, metric='euclidean')
    max_n_indices = np.argpartition(all_distances.flatten(), -n)[-n:]
    max_n_2d_indices = np.unravel_index(max_n_indices, all_distances.shape)
    indices_arr1 = max_n_2d_indices[0]
    # Return the n maximum distances indices as a list
    # Convert to set and back to list to remove duplicates
    unique_indices = list(set(indices_arr1.tolist()))
    return unique_indices

# Class MLRATraining will only be used for training new models, not for predictions!
class MLRATraining:
    def __init__(self, main):
        self.m = main

    @staticmethod
    def cross_val_predict_with_std(X, y, model, cv=None):
        """
        Custom version of cross_val_predict that also computes prediction standard deviations.
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
    def _fit_hyper(X, y, model):
        stds = []
        # yield {"type": "progress", "progress": 0, "loop_counter": 1}
        model.fit(X, y)
        if isinstance(model, RandomizedSearchCV) and isinstance(model.best_estimator_, GaussianProcessRegressor):
            predictions, stds = model.best_estimator_.predict(X, return_std=True)
        else:
            predictions = model.best_estimator_.predict(X)
        best_hyperparams = model.best_params_
        yield {"type": "hyperparameters", "best_hyperparams": best_hyperparams}
        score = mean_squared_error(y, predictions, squared=False)
        yield {'type': 'result', 'model': model, 'performances': score, 'predictions': predictions, 'stds': stds,
               'X_val': X, 'y_val': y}

    @staticmethod
    def _fit_split(X, y, model, split_method="train_test_split", kfolds=5, test_size=0.2, random_state=42,
                   hypara_opt=False, param_grid=None):
        yield {"type": "progress", "progress": 0, "loop_counter": 1}
        if split_method == 'train_test_split':
            stds = []
            train_X, test_X, train_y, test_y = train_test_split(X, y, test_size=test_size, random_state=random_state)
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
        else:
            raise ValueError(f"Unrecognized split method: {split_method}")


    @staticmethod
    def _split(X, y, split_method="train_test_split", kfolds=5, test_size=0.2, random_state=42):
        if split_method == "train_test_split":
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
            yield X_train, X_test, y_train, y_test
        elif split_method == "kfold":
            kf = KFold(n_splits=kfolds, random_state=random_state, shuffle=True)
            for train_index, test_index in kf.split(X, y):
                yield X[train_index], X[test_index], y[train_index], y[test_index]
        else:
            raise ValueError(f"Unrecognized split method: {split_method}")
    
    @staticmethod
    def _al_loop_internal(X, y, model, init_percentage, split_method="train_test_split", kfolds=5, test_size=0.2):
        all_training_indices = []
        all_performances = []
        all_stds = []
        all_preds = []
        X_val, y_val = None, None
        loop_counter = 1
        for X_train, X_test, y_train, y_test in MLRATraining._split(X, y, split_method=split_method, kfolds=kfolds,
                                                                    test_size=test_size):
            # Get generator from _al_loop
            loop_gen = MLRATraining._al_loop(X_train, y_train, X_test, y_test, model, init_percentage=init_percentage)

            for output in loop_gen:
                if output['type'] == 'result':
                    all_training_indices.append(output['training_indices'])
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

        yield {'type': 'result', 'model': model, 'all_training_indices': all_training_indices,
               'performances': all_performances, 'predictions': all_preds, 'stds': all_stds, 'X_val': X_val, 'y_val': y_val}
        # return model, all_training_indices, all_performances, X_val, y_val
        
        
    @staticmethod
    def _al_loop(X, y, X_val, y_val, model, init_percentage):

        init_percentage = init_percentage/100
        n_samples = X.shape[0]
        n_init = int(init_percentage * n_samples)

        # Compute the pairwise distances between all samples
        distances = pairwise_distances(X)
        # Get the maximum distance for each sample
        max_distances = distances.max(axis=1)
        # Get the indices of the samples sorted by their maximum distance in descending order
        sorted_indices = np.argsort(max_distances)[::-1]
        # Select the initial indices as the top x% of the sorted indices
        initial_idx = sorted_indices[:n_init]
        # initial_idx = np.random.choice(range(len(X)), size=n_init, replace=False)  # random initial sampling

        X_initial, y_initial = X[initial_idx], y[initial_idx]

        model.fit(X_initial, y_initial)
        training_indices = list(initial_idx)
        performances = []

        initital_pred = model.predict(X_val)
        best_score = np.sqrt(mean_squared_error(y_val, initital_pred, squared=False))
        performances.append(best_score)

        remaining_indices = np.setdiff1d(np.arange(n_samples), training_indices)
        n_query = 1

        total_remaining = len(remaining_indices)
        last_printed = -1

        for i in range(len(remaining_indices)):

            remaining_X = X[remaining_indices]
            query_indices = max_euclidean_distances(remaining_X, X_initial, n=n_query)
            chosen_indices = remaining_indices[query_indices]

            X_initial = np.concatenate((X_initial, X[chosen_indices]))
            y_initial = np.concatenate((y_initial, y[chosen_indices]))
            training_indices.append(chosen_indices)

            model.fit(X_initial, y_initial)

            pred = model.predict(X_val)
            score = np.sqrt(mean_squared_error(y_val, pred, squared=False))
            performances.append(score)


            progress = (total_remaining - len(remaining_indices)) / total_remaining * 100
            if int(progress) % 5 == 0 and int(progress) != last_printed:
                # print('Progress: {:.0f}%'.format(progress))
                last_printed = int(progress)
                yield{'type': 'progress', 'progress': progress}

            if score > best_score:
                X_initial = np.delete(X_initial, -len(query_indices), axis=0)
                y_initial = np.delete(y_initial, -len(query_indices), axis=0)
                training_indices.pop(-len(query_indices))
                performances.pop()
            else:
                best_score = score
                # print('RMSE: {:.4f}'.format(best_score))

            remaining_indices = np.delete(remaining_indices, query_indices)
            # print(len(remaining_X))

        yield{'type': 'result', 'model': model, 'all_training_indices': training_indices, 'performances': performances,
              'X_val': X_val, 'y_val': y_val}


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
            "AGBdry": ["AGBdry", [0.0, 2000.0], 0.01],
            "AGBfresh": ["AGBfresh", [0.0, 5000.0], 0.001],
            "CWC": ["CWC", [0.0, 0.3], 1],
            "Nitrogen": ["Nitrogen", [0.0, 40], 0.1],
            "Carbon": ["Carbon", [0.0, 600], 0.01]
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


# Train new algorithm; at the moment, only MLPR can be used and the hyperparameters are fixed but the developers
# can always add new algorithms or change the parameters. The training process needs a working LUT that was created
# with "CreateLUT_core.py".
class ProcessorTraining:

    def __init__(self, main):
        self.m = main
        # these are the four PROSAIL parameters to be estimated. Mind the order!
        #self.para_list = ['LAI', 'LIDF', 'cab', 'cm']
        self.para_list = []
        self.noisetype = 1
        self.sigma = 4
        self.mlra = None
        self.ml_params = {}
        self.training_indices, self.performances = (None, None)

        # Parameterization (everything except ANN is deprecated)

        # Activation function     Solver      alpha (penalty) max. nr. of iterations
        # self.ann_activation, self.ann_solver, self.ann_alpha, self.ann_max_iter = (None, None, None, None)
        # self.gpr_kernel = None
        # self.svr_kernel, self.svr_C, self.svr_g = (None, None, None)
        # self.rf_n_estimators, self.rf_max_features, self.rf_min_samples_leaf = (None, None, None)
        # self.ml_params_dict_ann = None  # this is the init of a dictionary containing the hyperparameter of the ANN
        # self.ml_params_dict_svr = None
        # self.ml_params_dict_rforest = None
        # self.ml_params_dict_gpr = None
        self.all_results_dict = {}
        self.best_hyperparameters_dict = {}
        self.y_val_dict = {}


    def training_setup(self, lut_metafile, exclude_bands, npca, model_meta, para_list, noisetype=1, noiselevel=4,
                       algorithm='ANN',
                       use_al=False, use_insitu=False, n_initial=2,
                       perf_eval=False, split_method='train_test_split', kfolds=5, test_size=0.2, hyperp_tuning=False,
                       hyperparas_dict=None):
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

        # LUT
        self.get_meta_LUT(lut_metafile=lut_metafile)  # read meta information of the LUT to be trained
        self.splits = int(self.meta_dict['splits'])  # number of splits per geo-ensemble in the LUT
        self.conversion_factor = int(self.meta_dict['multiplication_factor'])  # LUT boost e.g. 10000 for EnMAP
        self.lut_metafile = lut_metafile  # full path to the LUT metafile
        self.lut_basedir = os.path.dirname(lut_metafile)  # basic directory in which the LUT is stored
        self.lut_base = self.lut_basedir + "/" + str(self.meta_dict['name'])  # base name of the LUT

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

        # Boosting the parameters is necessary for some algorithms which cannot handle very small or large values
        # for the training (e.g. ANN fails when learning y=0.004, so it is boosted to y=4 according to "Functions.conv"
        self.para_boost = False
        # if self.algorithm == 'ANN':
        #     self.para_boost = True
        # else: self.para_boost = False

        # Which scaler should be used?
        self.scaler = StandardScaler()  # create instance of standard scaler
        if npca > 0:
            self.pca = PCA(npca)  # create an instance of the PCA for the desired number of components
        else:
            self.pca = None

        self.components = npca  # how many components for the PCA? (0 if deactivated)

    def insitu_data_setup(self, val_data, npca):
        # Scaling and PCA dim reduction of insitu spectra
        self.y_val_dict = {key: val_data[key] for key in val_data if key not in ['Reflectance', 'Wavelengths']}
        X_val = val_data.get('Reflectance')
        wavelengths = val_data.get('Wavelengths')

        subset_bands = [i for i in range(len(wavelengths))
                                 if i not in self.exclude_bands]

        X_val = [X_val[i] for i in subset_bands]
        X_val = np.asarray(X_val).T

        self.scaler = StandardScaler()
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

    def validation_setup(self, val_file, exclude_bands, npca):
        self.val_file = val_file
        val_data = np.loadtxt(self.val_file, delimiter="\t", skiprows=1)
        X_val = val_data[2:, 1:].T / 10000
        self.y_val = val_data[0, 1:]

        self.exclude_bands = exclude_bands  # the bands to be excluded for the training (water vapor absorption etc.)

        self.scaler = StandardScaler()
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
            # Extract kernel parameters
            constant_value = self.ml_params.get('kernel__k1__k1__constant_value', 1.0)
            length_scale = self.ml_params.get('kernel__k1__k2__length_scale', 1.0)
            noise_level = self.ml_params.get('kernel__k2__noise_level', 1e-10)

            # Construct the kernel
            self.gpr_kernel = constant_value * RBF(length_scale=length_scale,
                                                   length_scale_bounds=(1e-5, 1e5)) + WhiteKernel(
                noise_level=noise_level)

            # Exclude the keys specific to kernel construction from the model's params
            model_params = {key: val for key, val in self.ml_params.items() if not key.startswith('kernel__')}

            # Update the 'kernel' argument with the constructed kernel
            model_params['kernel'] = self.gpr_kernel

            # Now initialize the GPR
            self.ml_model_ext = '.gpr'
            self.mlra = GaussianProcessRegressor(**model_params)

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
            self.mlra = self.init_hyperparameter_tuning(self.mlra, param_dist)

        # AL based on split (train-test-split or kfold cross val)
        if self.use_al and not self.use_insitu:
            self.al_paras = {'split_method': self.split_method, 'kfolds': self.kfolds, 'test_size': self.test_size,
                             'init_percentage': self.n_initial}
            self.ml_model = self.m.mlra_training._al_loop_internal

        # AL with external insitu data
        elif self.use_al and self.use_insitu:
            if self.y_val_dict:
                self.y_val = self.y_val_dict.get(var)

            self.al_paras = {'X_val': self.X_val, 'y_val': self.y_val,
                             'init_percentage': self.n_initial}

            self.ml_model = self.m.mlra_training._al_loop

        # No AL, training on splits
        elif not self.use_al and self.perf_eval and not self.hyperp_tuning:
            self.al_paras = {'split_method': self.split_method, 'kfolds': self.kfolds, 'test_size': self.test_size}
            self.ml_model = self.m.mlra_training._fit_split
        # No AL, training with hyperparameter tuning
        elif self.hyperp_tuning:
            self.al_paras = {}
            self.ml_model = self.m.mlra_training._fit_hyper
        # No AL, only training -> all samples
        else:
            self.ml_model = self.m.mlra_training._fit # construct the model and pass it to self.ml_model

    def init_hyperparameter_tuning(self, mlra, param_dist, n_iter_search=10, n_jobs=2):
        random_search = RandomizedSearchCV(mlra, param_distributions=param_dist, n_iter=n_iter_search,
                                           scoring='neg_mean_squared_error', n_jobs=n_jobs, cv=self.kfolds,
                                           verbose=2, random_state=42)
        return random_search



    def train_and_dump(self, prgbar_widget=None, qgis_app=None):
        # Train a model and dump the trained model to a file in the model directory

        # Number of models to be trained and dumped: one model per geo-ensemble and parameter
        nmodels_total = self.npsi * self.ntto * self.ntts * len(self.para_list)

        # Train Model for each geo-ensemble
        for rAA in range(self.npsi):
            for OZA in range(self.ntto):
                for SZA in range(self.ntts):

                    # number of geo-ensemble, corresponds to name of the LUT-file
                    geo_ensemble = rAA * self.ntto * self.ntts + OZA * self.ntts + SZA
                    X, y = self.read_lut(geo=geo_ensemble)  # read reflectances (X) and PROSAIL parameters (y) from LUT

                    if self.noisetype > 0:
                        X = self._add_noise(ref_list=X, noisetype=self.noisetype, sigma=self.sigma,
                                            conversion=self.conversion_factor)

                    # Train and dump individual model per parameter
                    for ipara, para in enumerate(self.para_list):

                        model_no = geo_ensemble * len(self.para_list) + ipara + 1  # serial number of model

                        if self.use_al and not self.use_insitu: prg_al_string = 'internal AL'
                        elif self.use_al and self.use_insitu: prg_al_string = 'insitu AL'
                        elif self.hyperp_tuning: prg_al_string = 'hyperparams tuned'
                        else: prg_al_string = 'non AL'

                        if self.hyperparas_dict:
                            hyperparams = self.hyperparas_dict
                        else:
                            hyperparams = {}

                        self.init_model(var=para, hyperparams=hyperparams)  # initialize the model with the given settings

                        # Update progress bar
                        if prgbar_widget:
                            if prgbar_widget.gui.lblCancel.text() == "-1":
                                prgbar_widget.gui.lblCancel.setText("")
                                prgbar_widget.gui.cmdCancel.setDisabled(False)
                                raise ValueError("Training cancelled!")

                            prgbar_widget.gui.lblCaption_r.setText(
                                'Training {} {} model {:d} of {:d}: {}'.format(
                                    prg_al_string, self.algorithm, model_no, nmodels_total, para))
                            qgis_app.processEvents()
                        else:
                            print("Training {} {} Noise {:d}-{:d} | {} | Geo {:d} of {:d}".format(prg_al_string,
                            self.algorithm, self.noisetype, self.sigma, para, geo_ensemble + 1,
                            self.ntts * self.ntto * self.npsi))

                        if self.scaler:  # if X (reflectances) are to be scaled
                            self.scaler.fit(X)  # fit scaler
                            x = self.scaler.transform(X)  # transform scaler
                        else:
                            x = np.copy(X)  # consecutive code needs x instead of X; copy if no scaler is used

                        # fit and transform a PCA
                        if self.pca:
                            self.pca.fit(x)#, y[:, ipara])
                            x = self.pca.transform(x)

                        if self.perf_eval:  # performance evaluation

                            for result_dict in self.ml_model(
                                    X=x, y=y[:, ipara], model=self.mlra, **self.al_paras):
                                if result_dict["type"] == "result":  # results are ready, populate results
                                    model = result_dict["model"]
                                    self.X_val = result_dict["X_val"]
                                    self.y_val = result_dict["y_val"]
                                    performances = np.array(result_dict["performances"])
                                    temp_dict = {}
                                    if self.use_insitu and self.algorithm == 'GPR':
                                        predictions, stds = model.predict(self.X_val, return_std=True)
                                        temp_dict['stds'] = stds
                                    elif self.use_insitu and self.algorithm != 'GPR':
                                        predictions = model.predict(self.X_val)
                                    else:
                                        predictions = np.array(result_dict["predictions"])

                                    if self.para_boost:
                                        # bring results back to original scale:
                                        self.y_val = self.y_val / self.m.func.conv[para][2]
                                        performances = performances / self.m.func.conv[para][2]
                                        predictions = predictions / self.m.func.conv[para][2]

                                    temp_dict = {
                                        "X_val": self.X_val,
                                        "y_val": self.y_val,
                                        "performances": performances,
                                        "predictions": predictions}
                                    # GPR yields stds
                                    if 'stds' in result_dict:
                                        stds = np.array(result_dict['stds'])
                                        if self.para_boost:
                                            stds = stds / self.m.func.conv[para][2]
                                        temp_dict['stds'] = stds
                                    if self.use_al:
                                        # TODO: these indices point at AL selected spectra -> export
                                        training_indices = result_dict["all_training_indices"]
                                        temp_dict["training_indices"] = training_indices
                                    self.all_results_dict[f'{para} {prg_al_string} {self.algorithm}'] = temp_dict

                                elif result_dict["type"] == "hyperparameters":
                                    if self.algorithm not in self.best_hyperparameters_dict:
                                        self.best_hyperparameters_dict[self.algorithm] = {}

                                    self.best_hyperparameters_dict[self.algorithm][para] = {
                                        'hyperparas': result_dict["best_hyperparams"]}

                                elif result_dict["type"] == "progress":  # progressbar updates

                                    progress = result_dict['progress']
                                    # loop_counter = result_dict['loop_counter']
                                    if prgbar_widget:
                                        prgbar_widget.gui.prgBar.setValue(int(progress))
                                        qgis_app.processEvents()
                                    else:
                                        print('Progress: {:d}%'.format(int(progress)))

                            # final_pred, pred_std = model.predict(self.X_val, return_std=True)
                            # if self.algorithm == 'GPR':
                            #     out_pred = np.array([self.y_val, predictions, stds])
                            # else:
                            #     out_pred = np.array([self.y_val, predictions])

                            if isinstance(performances, list):  # weird exception handling
                                for element in performances:
                                    if isinstance(element, list):
                                        if len(performances[0]) == 1:
                                            performances = np.asarray(performances).reshape((1, 1))

                            # np.save("E:\Testdaten/performances_{}".format(str(para)), performances)
                            # np.save("E:\Testdaten/results_{}".format(str(para)), out_pred)

                            # if self.hyperp_tuning:
                            #     print("Best parameters found: ", self.mlra.best_params_)
                            #     print("Lowest RMSE found: ", np.sqrt(np.abs(self.mlra.best_score_)))

                        else:
                            model = self.ml_model(X=x, y=y[:, ipara], model=self.mlra)

                        joblib.dump(model, self.model_base + "_{:d}_{}{}".format(
                            geo_ensemble, para, self.ml_model_ext))  # dump (save) model to file for later use

                        # if self.hyperp_tuning:
                        #     joblib.dump(self.best_hyperparameters_dict,
                        #                 self.model_base + '_{:d}_{}_{}.hyper'.format(geo_ensemble, self.algorithm,
                        #                                                         para))

                        if not self.use_al and len(self.para_list) > 1:
                            prgbar_widget.gui.prgBar.setMaximum(100)
                            prgbar_widget.gui.prgBar.setValue(int(model_no/nmodels_total*100))
                            qgis_app.processEvents()

        # Not Done yet! Save further information to the base-folder: information about scaler and pca
        # are saved to a .proc-file; this file is read before calling predict on a model to prepare spectral data
        # the same way as the LUT-spectra were preprocessed in this routine; there is one .proc-file per parameter,
        # since scaler and pca can/does vary between parameters; however: at the time being, scaler and PCA are the
        # same for all parameters and are saved as copies
        for para in self.para_list:
            processing_dict = {"scaler": self.scaler, "pca": self.pca}
            joblib.dump(processing_dict, self.model_base + '_{}.proc'.format(para))  # dump the .proc-file as well

        # Write Model Meta
        with open(self.model_metafile, 'w') as para_file:  # Meta-information; one meta-file for all paras!
            para_file.write("alg={}\nnoisetype={:d}\nsigma={:d}\nPCA_components={:d}\nscaler={}"
                            .format(self.algorithm, self.noisetype, self.sigma, self.components, str(self.scaler)))
            para_file.write("\ntarget_parameters=" + ";".join(str(i) for i in self.para_list))
            para_file.write("\ntts=" + ";".join(str(i) for i in self.tts))
            para_file.write("\ntto=" + ";".join(str(i) for i in self.tto))
            para_file.write("\npsi=" + ";".join(str(i) for i in self.psi))
            para_file.write("\nexclude_bands=" + ";".join(str(i) for i in self.exclude_bands))
            if self.use_al:
                para_file.write("\nactive_learning=" + ";".join(str(self.use_al)))
            if self.hyperp_tuning:
                para_file.write("\nbest_hyperparameters=" + str(
                    self.best_hyperparameters_dict[self.algorithm]))

        if self.hyperp_tuning:
            # print(self.best_hyperparameters_dict)
            joblib.dump(self.best_hyperparameters_dict,
                        self.model_base + '.hyper')

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
                           + lut[self.para_dict['cbc'], :]) * lut[self.para_dict['LAI'], :]  * 10000
            if para == 'AGBfresh':
                y[:, i] = (lut[self.para_dict['cp'], :] + lut[self.para_dict['cbc'], :]
                           + lut[self.para_dict['cw'], :]) * lut[self.para_dict['LAI'], :] * 10000
            if para == 'CWC':
                y[:, i] = lut[self.para_dict['cw'], :] * lut[self.para_dict['LAI'], :]
            if para == 'Nitrogen':
                y[:, i] = (lut[self.para_dict['LAI'], :] * lut[self.para_dict['cp'], :]) * 10000 / 4.43
            if para == 'Carbon':
                y[:, i] = (lut[self.para_dict['LAI'], :] * lut[self.para_dict['cbc'], :]) * 10000 / 2.31

            if self.para_boost and para in self.para_dict:  # to boost or not to boost
                y[:, i] = lut[self.para_dict[para], :] * self.m.func.conv.get(para)[2]
            else:
                if para in self.para_dict:
                    y[:, i] = lut[self.para_dict[para], :]

        return X, y

    @staticmethod
    def _add_noise(ref_list, noisetype, sigma, conversion):
        # noise module to put a noise term on top of PROSAIL spectra

        # sigma (strength of the noise) is provided as %, so it needs to be converted to relative values
        # and optionally multiplied with the conversion factor to match reflectance value ranges for additive noise

        if noisetype == 0:    # no noise
            return ref_list
        elif noisetype == 1:  # gaussian noise
            noise_std = np.std(ref_list) * sigma / 100
            ref_noisy = np.random.normal(loc=0.0, scale=noise_std, size=ref_list.shape) + ref_list
        elif noisetype == 2:  # additive noise
            sigma_c = (sigma / 100) * conversion  # sigma converted (e.g. 0...1 -> 0...10000)
            ref_noisy = np.random.normal(loc=0.0, scale=sigma_c, size=ref_list.shape) + ref_list
        elif noisetype == 3:  # multiplicative noise
            ref_noisy = (1 + np.random.normal(loc=0.0, scale=sigma / 100, size=ref_list.shape)) * ref_list
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
                         geo_in, spatial_geo, paras, algorithm, fixed_geos=None, nodat=None):
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
        except: self.exclude_bands = []

        if prg_widget:
            prg_widget.gui.lblCaption_r.setText('Reading Geometry Image...')
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
        self.out_matrix = self.predict(image=in_matrix, whichModel_coords=whichModel_coords, out_matrix=self.out_matrix,
                                       prg_widget=prg_widget, qgis_app=qgis_app)

    def write_prediction(self):
        # Write the estimated parameters to file
        self.m.func.write_image(out_matrix=self.out_matrix, image_out=self.res_out, grid=self.grid,
                                out_mode=self.out_mode, nodat=self.nodat[2], paras_out=self.paras)

    def predict(self, image, whichModel_coords, out_matrix, prg_widget, qgis_app):
        # Delete the bands to be excluded (they were stored in the ML-metafile) so that it matches with how the
        # models were trained (during training, exclude_bands were ignored in the LUT)
        image = np.delete(image, self.exclude_bands, axis=0)
        nbands, nrows, ncols = image.shape  # update image shape

        # In Sklearn, prediction of multiple data inputs at once is possible, but not as a 2D-array
        # We need to "collapse" the second dimension and create one long dim as follows:
        image = image.reshape((nbands, -1))  # collapse rows and cols into 1 dimension
        image = np.swapaxes(image, 0, 1)     # place predictors into the right position (where sklearn expects them)

        # Do this for each PROSAIL parameter after another
        for ipara, para in enumerate(self.paras):
            if prg_widget:
                prg_widget.gui.lblCaption_r.setText('Predicting {} (parameter {:d} of {:d})...'
                                                    .format(para, ipara+1, len(self.paras)))
                qgis_app.processEvents()

            # Load the right model from drive; it's actually a .npz file, so the arrays of .proc can be
            # addressed like a dictionary; in the .proc-file the preprocession of the LUT is stored to perform
            # the same on the spectral image
            process_dict = joblib.load(self.model_dir + "/" + self.model_name + "_{}".format(para) + '.proc')
            #print(process_dict)

            # Make a copy of the input image and only work on that one to keep the original image.
            # This is memory expensive but better than loading image over and over again
            image_copy = np.copy(image).astype(dtype=np.float32)
            #print(image_copy.shape)

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

                # This is the core "predict" command in which the algorithm is asked to estimate from what it has learnt
                result = mod[imodel].predict(image_copy[whichModel_coords[i_imodel][0],
                                             whichModel_coords[i_imodel][1], :])

                # Convert the results and put it into the right position
                # out_matrix[parameter, row, col], row and col is stored in the coordinates of whichModel
                out_matrix[ipara, whichModel_coords[i_imodel][0], whichModel_coords[i_imodel][1]] = result  # / self.m.func.conv[para][2]

        return out_matrix


class ProcessorMainFunction:
    def __init__(self):
        self.mlra_training = MLRATraining(self)
        self.func = Functions(self)
        self.predict_main = ProcessorPrediction(self)
        self.train_main = ProcessorTraining(self)
