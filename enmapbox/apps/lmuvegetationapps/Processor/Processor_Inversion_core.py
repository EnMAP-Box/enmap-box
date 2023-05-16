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
                                                                                                                                                 *
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

from _classic.hubflow.core import *
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error
# from modAL.models import BayesianOptimizer
from lmuvegetationapps.Processor.modAL import ActiveLearner
from lmuvegetationapps.Processor.modAL.disagreement import *
# from modAL.uncertainty import uncertainty_sampling
# from modAL.disagreement import *
# from modAL.acquisition import max_EI, max_UCB, max_PI
# from ideal_v3 import ideal

import matplotlib as mpl
import matplotlib.pyplot as plt

import joblib

def GP_reg_std(regressor, X_actpool):
    _, std = regressor.predict(X_actpool, return_std=True)
    query_idx = np.argmax(std)
    return query_idx, X_actpool[query_idx]

# Class MLRATraining will only be used for training new models, not for predictions!
class MLRATraining:
    def __init__(self, main):
        self.m = main

    @staticmethod
    def _ann(X, y, activation, solver, alpha, max_iter):
        # This method calls and returns an MLP-Regressor based on the hyperparameters passed
        # It also fits ("trains") the model by assessing X (predictors, reflectances) and y (PROSAIL parameters)
        # So the result is a model that is ready to be used as in ".predict(new_x)"
        return MLPRegressor(activation=activation, solver=solver, alpha=alpha, max_iter=max_iter).fit(X, y)

    @staticmethod
    def _gpr(X, y, kernel):
        return GaussianProcessRegressor(kernel=kernel, copy_X_train=True, random_state=0).fit(X, y)

    @staticmethod
    def _al_gpr(X, y, kernel):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

        regressor = ActiveLearner(estimator=GaussianProcessRegressor(kernel=kernel, copy_X_train=True, random_state=0),
                                  query_strategy=edb,
                                  X_training=X_train, y_training=y_train)

        print("Train score: ", regressor.score(X_train, y_train))
        print("Test score: ", regressor.score(X_test, y_test))

        y_pred = regressor.predict(X_test)
        plt.scatter(y_test,y_pred)
        plt.show()

        return regressor

    @staticmethod
    def _al_gpr_internal(X, y, kernel):

        n_initial = int(2*len(X)/100)
        initial_idx = np.random.choice(range(len(X)), size=n_initial, replace=False)
        X_initial, y_initial = X[initial_idx], y[initial_idx]

        regressor = ActiveLearner(estimator=GaussianProcessRegressor(
            kernel=kernel, random_state=0, n_restarts_optimizer=1, normalize_y=True),
                                  query_strategy=edb, X_training=X_initial, y_training=y_initial)

        regressor_true = ActiveLearner(estimator=GaussianProcessRegressor(
            kernel=kernel, random_state=0, n_restarts_optimizer=1, normalize_y=True),
                                  query_strategy=edb, X_training=X_initial, y_training=y_initial)

        initial_predict = regressor.predict(X)
        initial_rmse = mean_squared_error(y, initial_predict)
        initial_score = regressor.score(X, y)
        X_pool = np.delete(X, initial_idx, axis=0)
        y_pool = np.delete(y, initial_idx)

        performance_history = [[initial_rmse], [initial_score]]
        n_queries = 50
        x_query_list = X[initial_idx]
        y_query_list = y[initial_idx]

        for idx in range(n_queries):
            print('Query no. %d' % (idx + 1))
            query_idx, query_instance = regressor.query(X_pool, n_instances=1)
            print(X_pool[query_idx].shape, y_pool[query_idx].shape)

            regressor.teach(X=X_pool[query_idx], y=y_pool[query_idx])
            predict = regressor.predict(X)
            rmse = mean_squared_error(y, predict)
            if rmse < performance_history[0][-1]:
                x_query_list = np.append(x_query_list, X_pool[query_idx], axis=0)
                y_query_list = np.append(y_query_list, y_pool[query_idx])
                performance_history[0] = np.append(performance_history[0], mean_squared_error(y, predict))
                performance_history[1] = np.append(performance_history[1], regressor.score(X, y))
                regressor_true.teach(X_pool[query_idx], y_pool[query_idx])
            else:
                regressor._fit_on_new(x_query_list, y_query_list)

            X_pool = np.delete(X_pool, query_idx, axis=0)
            y_pool = np.delete(y_pool, query_idx)
            print(len(X_pool))

        fig, ax = plt.subplots(figsize=(8.5, 6), dpi=130)
        ax2 = ax.twinx()

        ax.plot(performance_history[0], c='k')
        ax.scatter(range(len(performance_history[0])), performance_history[0], s=13, c='k', )
        ax2.plot(performance_history[1], c='r')
        ax2.scatter(range(len(performance_history[1])), performance_history[1], s=13, c='r')

        ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, integer=True))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=10))

        ax2.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=10))

        #ax.set_ylim(bottom=0, top=1)
        ax.grid(False)

        ax.set_xlabel('Number of iterations (max GPR-std sampling)', fontsize=16)
        ax.set_ylabel('LAI RMSE [m$^{2}$/m$^{2}$]', fontsize=16)
        ax2.set_ylabel('R² [-]', fontsize=16)
        ax.tick_params("both", labelsize=16)
        ax2.tick_params("y", labelsize=16)

        plt.tight_layout()
        plt.savefig(r"U:\EnVAL\Meetings\20_March_2023/AL_process.png", dpi=300)
        plt.show()

        print(performance_history)

        fig, ax = plt.subplots(figsize=(6, 6), dpi=130)
        ax.set_aspect('equal', adjustable='box')
        y_pred = regressor_true.predict(X)
        ax.scatter(y, y_pred, c='k', s=5)
        ax.plot([0, 1], [0, 1], 'k--', transform=ax.transAxes, )
        ax.tick_params("both", labelsize=16)
        ax.set_xlabel('LAI PROSAIL-PRO simulated [m$^{2}$/m$^{2}$]', fontsize=16)
        ax.set_ylabel('LAI estimated [m$^{2}$/m$^{2}$]', fontsize=16)
        ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=4, integer=True))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=4, integer=True))
        plt.tight_layout()
        plt.savefig(r"U:\EnVAL\Meetings\20_March_2023/LAI_GPR-AL_performance.png", dpi=300)
        plt.show()

    @staticmethod
    def _al_gpr_insitu(X, y, kernel, X_val, y_val):
        print(len(X))
        n_initial = int(2*len(X)/100)
        initial_idx = np.random.choice(range(len(X)), size=n_initial, replace=False)
        X_initial, y_initial = X[initial_idx], y[initial_idx]

        regressor = ActiveLearner(estimator=GaussianProcessRegressor(
            kernel=kernel, random_state=0),
                                  query_strategy=edb, X_training=X_initial, y_training=y_initial)

        regressor_true = ActiveLearner(estimator=GaussianProcessRegressor(
            kernel=kernel, random_state=0),
                                  query_strategy=edb, X_training=X_initial, y_training=y_initial)

        initial_predict = regressor.predict(X_val)
        initial_rmse = mean_squared_error(y_val, initial_predict)
        initial_score = regressor.score(X_val, y_val)
        X_pool = np.delete(X, initial_idx, axis=0)
        y_pool = np.delete(y, initial_idx)

        performance_history = [[initial_rmse], [initial_score]]
        n_queries = int(len(X)/n_initial)-1
        x_query_list = X[initial_idx]
        y_query_list = y[initial_idx]
        print(X_pool.shape)
        print(X_val.shape)

        for idx in range(n_queries):
            print('Query no. %d of %d' % (idx + 1, (n_queries)) )
            query_idx, query_instance = regressor.query(X_pool, n_instances=1)
            print(query_idx.shape)
            regressor.teach(X=X_pool[query_idx], y=y_pool[query_idx])
            predict = regressor.predict(X_val)
            rmse = mean_squared_error(y_val, predict)
            print(rmse)
            print(performance_history[0][-1])
            if rmse < performance_history[0][-1]:
                print("found")
                x_query_list = np.append(x_query_list, X_pool[query_idx], axis=0)
                y_query_list = np.append(y_query_list, y_pool[query_idx])
                performance_history[0] = np.append(performance_history[0], mean_squared_error(y_val, predict))
                performance_history[1] = np.append(performance_history[1], regressor.score(X_val, y_val))
                regressor_true.teach(X_pool[query_idx], y_pool[query_idx])
            else:
                regressor._fit_on_new(X=x_query_list, y=y_query_list)

            X_pool = np.delete(X_pool, query_idx, axis=0)
            y_pool = np.delete(y_pool, query_idx)
            print(len(X_pool))

        fig, ax = plt.subplots(figsize=(8.5, 6), dpi=130)
        ax2 = ax.twinx()

        ax.plot(performance_history[0], c='k')
        ax.scatter(range(len(performance_history[0])), performance_history[0], s=13, c='k', )
        ax2.plot(performance_history[1], c='r')
        ax2.scatter(range(len(performance_history[1])), performance_history[1], s=13, c='r')

        ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, integer=True))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=10))

        ax2.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=10))

        #ax.set_ylim(bottom=0, top=1)
        ax.grid(False)

        ax.set_xlabel('Number of iterations (max GPR-std sampling)', fontsize=16)
        ax.set_ylabel('LAI RMSE [m$^{2}$/m$^{2}$]', fontsize=16)
        ax2.set_ylabel('R² [-]', fontsize=16)
        ax.tick_params("both", labelsize=16)
        ax2.tick_params("y", labelsize=16)

        plt.tight_layout()
        plt.savefig(r"U:\EnVAL\Meetings\20_March_2023/AL_process.png", dpi=300)
        plt.show()

        print(performance_history)

        fig, ax = plt.subplots(figsize=(6, 6), dpi=130)
        ax.set_aspect('equal', adjustable='box')
        y_pred = regressor_true.predict(X_val)
        ax.scatter(y_val, y_pred, c='k', s=5)
        ax.plot([0, 1], [0, 1], 'k--', transform=ax.transAxes, )
        ax.tick_params("both", labelsize=16)
        ax.set_xlabel('LAI PROSAIL-PRO simulated [m$^{2}$/m$^{2}$]', fontsize=16)
        ax.set_ylabel('LAI estimated [m$^{2}$/m$^{2}$]', fontsize=16)
        ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=4, integer=True))
        ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=4, integer=True))
        plt.tight_layout()
        plt.savefig(r"U:\EnVAL\Meetings\20_March_2023/LAI_GPR-AL_performance.png", dpi=300)
        plt.show()

    @staticmethod
    def _al_gpr_ideal(X, y, kernel, X_val, y_val):

        pred_type = 'regression'
        n_init = int(2*len(X)/100)
        maxevals = int(30*len(X)/100)

        regressor = GaussianProcessRegressor(kernel=kernel, random_state=0)

        data = {"X": X, "Y": y, "X_test": X_val, "Y_test": y_val}

        trained_pred, samples, scores = ideal.ideal_training(data, regressor, pred_type, delta=5.,
                                                             n_init=n_init, maxevals=maxevals, method='ideal',
                                                             verbose=1)
        X_act = samples["X_act"]
        Y_act = samples["Y_act"]

        plt.figure(1)
        plt.semilogy(np.arange(n_init, maxevals) + 1, scores["test"][n_init:maxevals], linewidth=3)
        plt.title('RMSE on test data')
        plt.grid()
        plt.xlabel('queries')
        plt.draw()
        plt.show()

    # Add more ML-algorithms here in the same design if needed at any time (e.g. SVR, GPR, RandomForest, ...)


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
            "cbrown": ["brown_pigments", [0.0, 1.0], 10]}

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
        self.para_list = ['LAI', 'LIDF', 'cab', 'cm']

        # Parameterization (everything except ANN is deprecated)

        # Activation function     Solver      alpha (penalty) max. nr. of iterations
        self.ann_activation, self.ann_solver, self.ann_alpha, self.ann_max_iter = (None, None, None, None)
        self.gpr_kernel = None
        # self.svr_kernel, self.svr_C, self.svr_g = (None, None, None)
        # self.rf_n_estimators, self.rf_max_features, self.rf_min_samples_leaf = (None, None, None)
        self.ml_params_dict_ann = None  # this is the init of a dictionary containing the hyperparameter of the ANN
        # self.ml_params_dict_svr = None
        # self.ml_params_dict_rforest = None
        # self.ml_params_dict_gpr = None

    def training_setup(self, lut_metafile, exclude_bands, npca, model_meta, algorithm='ann', use_al=False):
        # Setup everything for training new models
        self.exclude_bands = exclude_bands  # the bands to be excluded for the training (water vapor absorption etc.)
        self.algorithm = algorithm  # name of the Algorithm ('ann' by default)
        self.use_al = use_al

        # LUT
        self.get_meta_LUT(lut_metafile=lut_metafile)  # read meta information of the LUT to be trained
        self.splits = int(self.meta_dict['splits'])  # number of splits per geo-ensemble in the LUT
        self.conversion_factor = int(self.meta_dict['multiplication_factor'])  # LUT boost e.g. 10000 for EnMAP
        self.lut_metafile = lut_metafile  # full path to the LUT metafile
        self.lut_basedir = os.path.dirname(lut_metafile)  # basic directory in which the LUT is stored
        self.lut_base = self.lut_basedir + "/" + self.meta_dict['name']  # base name of the LUT

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
        self.para_boost = True  # on per default

        # Add/multiply a noise term to LUT-spectra to gain more resilience towards real "noisy" spectra
        self.noise_type = 1  # 0: Off, 1: Additive, 2: Multiplicative
        self.sigma = 4  # std. of the noise in %

        # Which scaler should be used?
        self.scaler = StandardScaler()  # create instance of scaler; also: RobustScaler(),
                                        #                                  MinMaxScaler() -> need to be imported
        if npca > 0:
            self.pca = PCA(npca)  # create an instance of the PCA for the desired number of components
        else:
            self.pca = None

        self.components = npca  # how many components for the PCA? (0 if deactivated)

    def validation_setup(self, val_file, exclude_bands, npca,):
        self.val_file = val_file
        val_data = np.loadtxt(self.val_file, delimiter="\t", skiprows=1)
        X_val = val_data[1:, 1:].T
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

                    if self.noise_type > 0:
                        X = self._add_noise(ref_list=X, noise_type=self.noise_type, sigma=self.sigma,
                                            conversion=self.conversion_factor)

                    # Train and dump individual model per parameter
                    for ipara, para in enumerate(self.para_list):

                        model_no = geo_ensemble * len(self.para_list) + ipara + 1  # serial number of model

                        # Update progress bar
                        if prgbar_widget:
                            if prgbar_widget.gui.lblCancel.text() == "-1":
                                prgbar_widget.gui.lblCancel.setText("")
                                prgbar_widget.gui.cmdCancel.setDisabled(False)
                                raise ValueError("Training cancelled!")

                            prgbar_widget.gui.lblCaption_r.setText('Training model {:d} of {:d}'.format(model_no,
                                                                                                        nmodels_total))
                            qgis_app.processEvents()
                        else:  # if no progress bar exists, e.g. code is run from _exec.py
                            print("Training {} Noise {:d}-{:d} | {} | Geo {:d} of {:d}".format(
                                self.algorithm, self.noise_type, self.sigma, para, geo_ensemble + 1,
                                self.ntts * self.ntto * self.npsi))

                        self.init_model(var=para)  # initialize the model with the given settings

                        if self.scaler:  # if X (reflectances) are to be scaled
                            self.scaler.fit(X)  # fit scaler
                            x = self.scaler.transform(X)  # transform scaler
                        else:
                            x = np.copy(X)  # consecutive code needs x instead of X; copy if no scaler is used

                        # fit and transform a PCA
                        if self.pca:
                            self.pca.fit(x)#, y[:, ipara])
                            x = self.pca.transform(x)

                        model = self.ml_model(X=x, y=y[:, ipara], **self.ml_params)  # create instance of the model
                        joblib.dump(model, self.model_base + "_{:d}_{}{}".format(
                            geo_ensemble, para, self.ml_model_ext))  # dump (save) model to file for later use

                        if prgbar_widget:
                            prgbar_widget.gui.prgBar.setValue(int(model_no * 100 / nmodels_total))
                            qgis_app.processEvents()

        # Not Done yet! Save further information to the base-folder: information about scaler and pca
        # are saved to a .proc-file; this file is read before calling predict on a model to prepare spectral data
        # the same way as the LUT-spectra were preprocessed in this routine; there is one .proc-file per parameter,
        # since scaler and pca can/does vary between parameters; however: at the time being, scaler and PCA are the
        # same for all parameters and are saved as copies
        for para in self.para_list:
            processing_dict = {"scaler": self.scaler,
                               "pca": self.pca}

            joblib.dump(processing_dict, self.model_base + '_{}.proc'.format(para))  # dump the .proc-file as well

        # Write Model Meta
        with open(self.model_metafile, 'w') as para_file:  # Meta-information; one meta-file for all paras!
            para_file.write("alg={}\nnoise_type={:d}\nsigma={:d}\nPCA_components={:d}\nscaler={}"
                            .format(self.algorithm, self.noise_type, self.sigma, self.components, str(self.scaler)))
            para_file.write("\ntts=" + ";".join(str(i) for i in self.tts))
            para_file.write("\ntto=" + ";".join(str(i) for i in self.tto))
            para_file.write("\npsi=" + ";".join(str(i) for i in self.psi))
            para_file.write("\nexclude_bands=" + ";".join(str(i) for i in self.exclude_bands))

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

        for i, para in enumerate(self.para_list):  # extract parameters
            if self.para_boost:  # to boost or not to boost
                y[:, i] = lut[self.para_dict[para], :] * self.m.func.conv.get(para)[2]
            else:
                y[:, i] = lut[self.para_dict[para], :]

        return X, y

    @staticmethod
    def _add_noise(ref_list, noise_type, sigma, conversion):
        # noise module to put a noise term on top of PROSAIL spectra

        # sigma (strength of the noise) is provided as %, so it needs to be converted to relative values
        # and optionally multiplied with the conversion factor to match reflectance value ranges for additive noise
        sigma_c = (sigma/100) * conversion  # sigma converted (e.g. 0...1 -> 0...10000)

        if noise_type == 0:    # no noise
            return ref_list
        elif noise_type == 1:  # additive noise
            ref_noisy = np.random.normal(loc=0.0, scale=sigma_c, size=ref_list.shape) + ref_list
        elif noise_type == 2:  # multiplicative noise
            ref_noisy = (1 + np.random.normal(loc=0.0, scale=sigma / 100, size=ref_list.shape)) * ref_list
        else:
            return None
        ref_noisy[ref_noisy < 0] = 0  # stochastic process may happen to produce ref < 0 -> set to zero
        return ref_noisy

    def init_model(self, var):
        # method to initialize a model, i.e. prepare an algorithm before it sees any data

        # At the moment, only algorithm == 'ann' is implemented; add parameterization for other algorithms if necessary
        if self.algorithm == 'ann':
            # ANN
            if not self.ann_activation:  # if self.ann_activation is None, everything is None
                if var == "LIDF":  # hyperparameters best suited to estimate the ALIA
                    self.ann_activation = 'tanh'  # logistic, relu, identity, tanh
                    self.ann_solver = 'lbfgs'  # adam, lbfgs, sgd
                    self.ann_alpha = 10.0
                    self.ann_max_iter = 10000  # 5000
                elif var == "cab":  # hyperparameters best suited to estimate Cab
                    self.ann_activation = 'tanh'  # logistic, relu, identity, tanh
                    self.ann_solver = 'adam'  # adam, lbfgs, sgd
                    self.ann_alpha = 0.01
                    self.ann_max_iter = 10000  # 2000
                elif var == "cm":  # hyperparameters best suited to estimate LMA
                    self.ann_activation = 'logistic'  # logistic, relu, identity, tanh
                    self.ann_solver = 'lbfgs'  # adam, lbfgs, sgd
                    self.ann_alpha = 0.1
                    self.ann_max_iter = 10000  # 1000
                else:    # hyperparameters best suited to estimate LAI and all others
                    self.ann_activation = 'logistic'  # logistic, relu, identity, tanh
                    self.ann_solver = 'lbfgs'  # adam, lbfgs, sgd
                    self.ann_alpha = 1.0
                    self.ann_max_iter = 10000  #5000

            # make a dictionary from the hyperparams
            self.ml_params = {'activation': self.ann_activation, 'solver': self.ann_solver,
                              'alpha': self.ann_alpha, 'max_iter': self.ann_max_iter}
            self.ml_model_ext = '.ann'  # extension of the models to recognize it as a neural network model
            self.ml_model = self.m.mlra_training._ann  # construct the model and pass it to self.ml_model

        if self.algorithm == 'gpr':
            self.gpr_kernel = 1.0 * RBF(1.0) + WhiteKernel()
            self.ml_params = {'kernel': self.gpr_kernel}
            self.ml_model_ext = '.gpr'  # extension of the models to recognize it as a GPR model
            self.ml_model = self.m.mlra_training._gpr  # construct the model and pass it to self.ml_model

        if self.algorithm == 'al_gpr':
            self.gpr_kernel = 1.0 * RBF(1.0) + WhiteKernel()
            self.ml_params = {'kernel': self.gpr_kernel}
            self.ml_model_ext = '.al_gpr'  # extension of the models to recognize it as a GPR model
            self.ml_model = self.m.mlra_training._al_gpr  # construct the model and pass it to self.ml_model

        if self.algorithm == 'al_gpr_internal':
            self.gpr_kernel = 1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-05, 1000000.0)) + WhiteKernel()
            self.ml_params = {'kernel': self.gpr_kernel}
            self.ml_model_ext = '.al_gpr_internal'  # extension of the models to recognize it as a GPR model
            self.ml_model = self.m.mlra_training._al_gpr_internal  # construct the model and pass it to self.ml_model

        if self.algorithm == 'al_gpr_insitu':
            self.gpr_kernel = 1.0 * RBF(1.0) + WhiteKernel()
            self.ml_params = {'kernel': self.gpr_kernel, 'X_val': self.X_val, 'y_val': self.y_val}
            self.ml_model_ext = '.al_gpr_insitu'  # extension of the models to recognize it as a GPR model
            self.ml_model = self.m.mlra_training._al_gpr_insitu  # construct the model and pass it to self.ml_model

        if self.algorithm == 'al_gpr_ideal':
            self.gpr_kernel = 1.0 * RBF(1.0) + WhiteKernel()
            self.ml_params = {'kernel': self.gpr_kernel, 'X_val': self.X_val, 'y_val': self.y_val}
            self.ml_model_ext = '.al_gpr_ideal'  # extension of the models to recognize it as a GPR model
            self.ml_model = self.m.mlra_training._al_gpr_ideal  # construct the model and pass it to self.ml_model




# Class to handle predicting variables from spectral reflectances with pre-trained Machine Learning (ML) algorithms
# At the moment, only ANNs are implemented, but potentially this script could be appended by any other ML-algo
class ProcessorPrediction:
    def __init__(self, main):
        self.m = main

        # Some basic information about the algorithm; svr is added just for the sake of demonstration
        self.mlra_meta = {'ann':
                              {'name': 'ann',
                               'file_ext': '.ann',
                               'file_name': 'ann_mlp'},
                          'gpr':
                              {'name': 'gpr',
                               'file_ext': '.gpr',
                               'file_name': 'gpr_mlp'}}

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
        self.algorithm = algorithm  # 'ann' at the moment, but possibly other algorithms, too

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
        self.all_tts = [float(i) for i in metacontent[5].split("=")[1].split(";")]
        self.all_tto = [float(i) for i in metacontent[6].split("=")[1].split(";")]
        self.all_psi = [float(i) for i in metacontent[7].split("=")[1].split(";")]
        try:
            self.exclude_bands = [int(i) for i in metacontent[8].split("=")[1].split(";")]
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
        # as an argument!                                                                           vvvvvvvvvv
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
                mod.append(joblib.load(self.model_dir + "/" + self.model_name + '_{:d}_{}'.format(igeo, para) + '.' + self.algorithm))

            # Browse through all models that were trained
            for i_imodel, imodel in enumerate(self.whichModel_unique):
                if whichModel_coords[i_imodel][0].size == 0:
                    continue  # after masking, not all 'imodels' are present in the image_copy

                # This is the core "predict" command in which the algorithm is asked to estimate from what it has learnt
                result = mod[imodel].predict(image_copy[whichModel_coords[i_imodel][0],
                                             whichModel_coords[i_imodel][1], :])

                # Convert the results and put it into the right position
                # out_matrix[parameter, row, col], row and col is stored in the coordinates of whichModel
                out_matrix[ipara, whichModel_coords[i_imodel][0], whichModel_coords[i_imodel][1]] = \
                    result / self.m.func.conv[para][2]

        return out_matrix


class ProcessorMainFunction:
    def __init__(self):
        self.mlra_training = MLRATraining(self)
        self.func = Functions(self)
        self.predict_main = ProcessorPrediction(self)
        self.train_main = ProcessorTraining(self)
