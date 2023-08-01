# -*- coding: utf-8 -*-
"""
***************************************************************************
    Processor_Inversion_core.py - LMU Agri Apps - Training of new ML-Models
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

This script handles the GUI for training new ML-models. There is no maximum flexibility as in the _core module,
because the user may not change the important hyperparameters on his own. There is only the possibility to create new
models on basis of individual Lookup-Tables.

"""

import sys
import os

import numpy as np

#ensure to call QGIS before PyQtGraph
from qgis.PyQt.QtWidgets import *
import lmuvegetationapps.Processor.Processor_Inversion_core as processor
from lmuvegetationapps import APP_DIR
from _classic.hubflow.core import *

from enmapbox.gui.utils import loadUi

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QVBoxLayout

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from mpl_toolkits.axes_grid1 import make_axes_locatable

pathUI_train = os.path.join(APP_DIR, 'Resources/UserInterfaces/Processor_Train.ui')
pathUI_wavelength = os.path.join(APP_DIR, 'Resources/UserInterfaces/Select_Wavelengths.ui')
pathUI_prgbar = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')
pathUI_Performance = os.path.join(APP_DIR, 'Resources/UserInterfaces/Processor_Performance_View.ui')


class MLTrainingGUI(QDialog):
    def __init__(self, parent=None):
        super(MLTrainingGUI, self).__init__(parent)
        loadUi(pathUI_train, self)


class SelectWavelengthsGUI(QDialog):
    def __init__(self, parent=None):
        super(SelectWavelengthsGUI, self).__init__(parent)
        loadUi(pathUI_wavelength, self)


class PRG_GUI(QDialog):
    def __init__(self, parent=None):
        super(PRG_GUI, self).__init__(parent)
        loadUi(pathUI_prgbar, self)
        self.allow_cancel = False

    def closeEvent(self, event):
        if self.allow_cancel:
            event.accept()
        else:
            event.ignore()


class Performance_GUI(QDialog):
    def __init__(self, parent=None):
        super(Performance_GUI, self).__init__(parent)
        loadUi(pathUI_Performance, self)


# MLTraining is a GUI handler for training new ML-models. For more information, go to Processor_Inversion_core.py
class ML_Training:
    def __init__(self, main):
        self.main = main
        self.gui = MLTrainingGUI()
        self.initial_values()
        self.params_dict_check()
        self.connections()

    def initial_values(self):
        # exclude_wavelengths: from ... to [nm]; these are default values for atmospheric water vapor absorption
        self.exclude_wavelengths = [[1290, 1525], [1730, 1970], [2400, 2500]]
        self.lut_path = None  # file path to the LUT metafile
        self.meta_dict = None  # intial empty dictionary for LUT meta
        self.wunit = "nanometers"
        self.wl, self.nbands, self.nbands_valid = (None, None, None)
        self.out_dir = None  # directory for output
        self.model_name = None  # name of the output model
        self.noisetype = 1
        self.noiselevel = 4
        self.use_al = False
        self.use_insitu = False
        self.split_method = 'train_test_split'
        self.kfolds = None
        self.test_size = None
        self.perf_eval = False
        self.n_initial = None
        self.algorithm = 'ANN'
        self.param_flags = [-1] * 12
        self.para_list = None

    def connections(self):
        self.gui.cmdInputLUT.clicked.connect(lambda: self.open_lut())
        self.gui.cmdModelDir.clicked.connect(lambda: self.get_folder())
        self.gui.cmdRun.clicked.connect(lambda: self.run_training())
        self.gui.cmdClose.clicked.connect(lambda: self.gui.close())

        self.gui.cmdExcludeBands.clicked.connect(lambda: self.open_wavelength_selection())
        self.gui.cmbPCA.toggled.connect(lambda: self.handle_pca())
        # Art. Noise Radio Button Group
        self.gui.radNoiseOff.clicked.connect(lambda: self.select_noise(mode=0))  # off
        self.gui.radNoiseAdd.clicked.connect(lambda: self.select_noise(mode=1))  # additive
        self.gui.radNoiseGauss.clicked.connect(lambda: self.select_noise(mode=2))  # gaussian
        # ML Algorithms Radio Button Group
        self.gui.rbANN.clicked.connect(lambda: self.handle_algorithm(mode=0))  # 0: ANN
        self.gui.rbGPR.clicked.connect(lambda: self.handle_algorithm(mode=1))  # 1: GPR
        self.gui.rbRFR.clicked.connect(lambda: self.handle_algorithm(mode=2))  # 2: RFR
        self.gui.rbSVR.clicked.connect(lambda: self.handle_algorithm(mode=3))  # 3: SVR
        self.gui.rbKRR.clicked.connect(lambda: self.handle_algorithm(mode=4))  # 4: KRR
        self.gui.rbGBR.clicked.connect(lambda: self.handle_algorithm(mode=5))  # 5: GBR

        self.gui.radAL.toggled.connect(lambda: self.handle_AL())
        self.gui.radNoAL.toggled.connect(lambda: self.handle_AL())

        self.gui.radInternal.toggled.connect(lambda: self.handle_AL_strat(mode='internal'))
        self.gui.radInsitu.toggled.connect(lambda: self.handle_AL_strat(mode='insitu'))

        self.gui.radPerf.toggled.connect(lambda: self.handle_PerfEval())
        self.gui.radNoPerf.toggled.connect(lambda: self.handle_PerfEval())

        self.gui.radTrainTest.toggled.connect(lambda: self.handle_PerfEvalStrat())
        self.gui.radCrossVal.toggled.connect(lambda: self.handle_PerfEvalStrat())

        for para in self.paramsdict:
            self.paramsdict[para].stateChanged.connect(lambda group, pid=para:
                                                       self.params_toggle(group="targets", para_id=pid))

    def params_toggle(self, para_id, group):
        if group == 'targets':
            # If checkbox checked, prepare param to be included for training
            self.param_flags[para_id] *= -1

    @staticmethod
    def toggle_params(param_flags):
        # Prepare target parameters from Boolean list
        all_labels = ["cab", "car", "anth", "cw", "cp", "cbc", "LAI", "AGBdry", "AGBfresh", "CWC", "Nitrogen", "Carbon"]
        # sort out only the labels for the indices which should be calculated
        para_list = [all_labels[i] for i in range(len(all_labels)) if param_flags[i] == 1]
        return para_list

    def enable_all(self):
        self.gui.cmbPCA.setEnabled(True), self.gui.cmbPCA.setChecked(True), self.gui.Noise_Box.setEnabled(True),
        self.gui.Paras_Box.setEnabled(True), self.gui.AL_Box.setEnabled(True), self.gui.Perf_Box.setEnabled(True),
        self.gui.ML_Box.setEnabled(True), self.gui.rbANN.setEnabled(True), self.gui.rbGPR.setEnabled(True),
        self.gui.rbRFR.setEnabled(True), self.gui.rbSVR.setEnabled(True), self.gui.rbKRR.setEnabled(True),
        self.gui.rbGBR.setEnabled(True)

    def handle_algorithm(self, mode):
        algorithm_dict = {0: 'ANN', 1: 'GPR', 2: 'RFR', 3: 'SVR', 4: 'KRR', 5: 'GBR'}
        self.algorithm = algorithm_dict[mode]

    def handle_AL(self):
        if self.gui.radAL.isChecked():
            self.gui.AL_rbFrame.setEnabled(True), self.gui.lblInitSamples.setEnabled(True),
            self.gui.sbInitSamples.setEnabled(True), self.gui.lblSelectOut.setEnabled(True),
            self.gui.txtSelectOut.setEnabled(True), self.gui.cmdSelectOut.setEnabled(True),
            self.gui.radPerf.setChecked(True), self.gui.radNoPerf.setEnabled(False),
            self.gui.radCrossVal.setEnabled(False), self.gui.radTrainTest.setChecked(True)
        if self.gui.radNoAL.isChecked():
            self.gui.AL_rbFrame.setEnabled(False), self.gui.lblInitSamples.setEnabled(False),
            self.gui.sbInitSamples.setEnabled(False), self.gui.lblSelectOut.setEnabled(False),
            self.gui.txtSelectOut.setEnabled(False), self.gui.cmdSelectOut.setEnabled(False),
            self.gui.radNoPerf.setEnabled(True), self.gui.radInternal.setChecked(True),
            self.gui.radNoPerf.setChecked(True)

    def handle_AL_strat(self, mode):
        if mode == 'internal':
            self.gui.frame_PerfEvalOptions.setEnabled(True), self.gui.radTrainTest.setEnabled(True),
            self.gui.radCrossVal.setEnabled(False), self.gui.lblTrainSize.setEnabled(True),
            self.gui.txtTrainSize.setEnabled(True),
        if mode == 'insitu':
            self.gui.frame_PerfEvalOptions.setEnabled(False)

    def handle_PerfEval(self):
        if self.gui.radPerf.isChecked():
            if self.gui.radInsitu.isChecked():
                self.gui.frame_PerfEvalOptions.setEnabled(False)
            else:
                self.gui.frame_PerfEvalOptions.setEnabled(True),
                self.gui.radTrainTest.setEnabled(True), self.gui.radCrossVal.setEnabled(True),
                self.gui.lblTrainSize.setEnabled(True), self.gui.txtTrainSize.setEnabled(True)
        if self.gui.radNoPerf.isChecked():
            self.gui.radTrainTest.setChecked(True),
            self.gui.radTrainTest.setEnabled(False), self.gui.radCrossVal.setEnabled(False),
            self.gui.lblTrainSize.setEnabled(False), self.gui.txtTrainSize.setEnabled(False),
            self.gui.lblFolds.setEnabled(False), self.gui.txtFolds.setEnabled(False)

    def handle_PerfEvalStrat(self):
        if self.gui.radTrainTest.isChecked():
            self.gui.lblTrainSize.setEnabled(True), self.gui.txtTrainSize.setEnabled(True),
            self.gui.lblFolds.setEnabled(False), self.gui.txtFolds.setEnabled(False)
        if self.gui.radCrossVal.isChecked():
            self.gui.lblTrainSize.setEnabled(False), self.gui.txtTrainSize.setEnabled(False),
            self.gui.lblFolds.setEnabled(True), self.gui.txtFolds.setEnabled(True)


    def open_lut(self, lutpath):  # open and read a lut-metafile
        if not __name__ == '__main__':
            result = str(QFileDialog.getOpenFileName(caption='Select LUT meta-file', filter="LUT-file (*.lut)")[0])
            if not result:
                return
            self.lut_path = result
        else:
            result = lutpath
            self.lut_path = lutpath

        self.gui.lblInputLUT.setText(result)

        with open(self.lut_path, 'r') as meta_file:
            content = meta_file.readlines()
            content = [item.rstrip("\n") for item in content]
        # This splits the keys and values in the meta file and extracts the values separated by ";"
        keys, values = list(), list()
        [[x.append(y) for x, y in zip([keys, values], line.split(sep="=", maxsplit=1))] for line in content]
        values = [value.split(';') if ';' in value else value for value in values]
        self.meta_dict = dict(zip(keys, values))  # file the metadata dictionary

        # wavelengths of the LUT are stored in the LUT-meta
        self.wl = np.asarray(self.meta_dict['wavelengths']).astype(np.float32)
        self.nbands = len(self.wl)
        # default wavelength ranges to be excluded are defined in __init__ and now with the metadata
        # of the spectral image, the respective "exclude bands" can be found
        self.exclude_bands = [i for i in range(len(self.wl)) if self.wl[i] < 400 or self.wl[i] > 2500
                              or self.exclude_wavelengths[0][0] <= self.wl[i] <= self.exclude_wavelengths[0][1]
                              or self.exclude_wavelengths[1][0] <= self.wl[i] <= self.exclude_wavelengths[1][1]
                              or self.exclude_wavelengths[2][0] <= self.wl[i] <= self.exclude_wavelengths[2][1]]
        self.gui.txtExclude.setText(" ".join(str(i) for i in self.exclude_bands))  # join to string for lineEdit
        self.gui.txtExclude.setCursorPosition(0)
        self.nbands_valid = self.nbands - len(self.exclude_bands)
        self.enable_all()

    def params_dict_check(self):
        self.paramsdict = {0: self.gui.chkCab, 1: self.gui.chkCcx, 2: self.gui.chkCanth,
                           3: self.gui.chkCw,  4: self.gui.chkCp, 5: self.gui.chkCBC,
                           6: self.gui.chkLAI, 7: self.gui.chkAGBdry, 8: self.gui.chkAGBfresh,
                           9: self.gui.chkCWC, 10: self.gui.chkNitrogen, 11: self.gui.chkCarbon}

    def open_wavelength_selection(self):
        # Handle opening the GUI for adding/excluding wavelengths from the list
        try:
            self.invoke_selection()
        except ValueError as e:
            self.abort(message=str(e))

    def invoke_selection(self):
        # Open the GUI for adding/excluding wavelengths from the list
        if self.lut_path is None:
            raise ValueError('Specify Lookup-Table first')
        elif not os.path.isfile(self.lut_path):
            raise ValueError('Lookup-Table not found: {}'.format(self.lut_path))

        pass_exclude = list()  # list of bands that are passed to be excluded by default, empty at first
        if not self.gui.txtExclude.text() == "":  # lineEdit is NOT empty, so some information is already there
            try:
                pass_exclude = self.gui.txtExclude.text().split(" ")  # get whats in the field
                pass_exclude = [int(pass_exclude[i])-1 for i in range(len(pass_exclude))]  # convert the text to int
            except ValueError:  # lineEdit contains crap
                self.gui.txtExclude.setText("")
                pass_exclude = list()

        self.main.select_wavelengths.populate(default_exclude=pass_exclude)
        self.main.select_wavelengths.gui.setModal(True)
        self.main.select_wavelengths.gui.show()

    def handle_pca(self):
        # Fitting a PCA is optional; if the option is selected, the user also needs to provide the number of components
        if self.gui.cmbPCA.isChecked():
            self.gui.spnPCA.setEnabled(True)
            # Set the default value for PCA components: 1 component for less than 5 bands, 5 for l.t. 15 and so on
            if self.nbands_valid < 5:
                self.npca = 1
            elif 5 < self.nbands_valid <= 15:
                self.npca = 5
            elif 15 < self.nbands_valid <= 120:
                self.npca = 10
            else:
                self.npca = 20
            self.gui.spnPCA.setValue(self.npca)  # place the value in the spinBox of the GUI
        if not self.gui.cmbPCA.isChecked():
            self.gui.spnPCA.setDisabled(True)
            self.npca = 0

    def select_noise(self, mode):
        # Enables and disables lineEdit for noise level
        if mode == 0:
            self.gui.txtNoiseLevel.setDisabled(True)
        else:
            self.gui.txtNoiseLevel.setDisabled(False)
        self.noisetype = mode

    def get_folder(self, path):
        # The model folder is important, as it contains all files needed
        if not __name__ == '__main__':
            path = str(QFileDialog.getExistingDirectory(caption='Select Output Directory for Model'))
            if not path:
                return
        else:  # test-case
            self.out_dir = path
            self.gui.txtModelName.setText("test")
            self.model_name = self.gui.txtModelName.text()
        if path:
            self.gui.txtModelDir.setText(path)
            self.out_dir = self.gui.txtModelDir.text().replace("\\", "/")
            if not self.out_dir[-1] == "/":  # last letter of the folder name needs to be a slash to add filenames
                self.out_dir += "/"

    def check_and_assign(self):
        if not self.lut_path:
            raise ValueError("A Lookup-Table metafile needs to be selected!")
        if not self.out_dir:
            raise ValueError("Output directory is missing")
        if not os.path.isdir(self.out_dir):
            raise ValueError("Output directory does not exist!")
        if self.gui.txtModelName.text() == "":
            raise ValueError("Please specify a name for the model")
        else:
            self.model_name = self.gui.txtModelName.text()
            self.model_meta = self.out_dir + self.model_name + '.meta'

        if not self.noisetype == 0:
            if self.gui.txtNoiseLevel.text() == "":
                raise ValueError('Please specify level for artificial noise')

            else:
                self.noiselevel = self.gui.txtNoiseLevel.text()
                try:
                    self.noiselevel = int(self.noiselevel)
                except ValueError:
                    raise ValueError('Cannot interpret noise level as decimal number')

        if self.gui.spnPCA.isEnabled():
            self.npca = self.gui.spnPCA.value()
            if self.npca > self.nbands_valid:
                raise ValueError("Model cannot be trained with {:d} components if LUT has only {:d} "
                                 "bands ({:d} minus {:d} excluded)".format(self.npca, self.nbands_valid, self.nbands,
                                                                           len(self.exclude_bands)))
        else:
            self.npca = 0

        if all(flag == -1 for flag in self.param_flags):
            raise ValueError("No target parameters selected")
        else:
            self.para_list = self.toggle_params(param_flags=self.param_flags)

        if self.gui.radAL.isChecked():
            self.use_al = True
            self.n_initial = self.gui.sbInitSamples.value()
        else:
            self.use_al = False
        if self.gui.radInsitu.isChecked():
            self.use_insitu = True
        else:
            self.use_insitu = False
        if self.gui.radPerf.isChecked():
            self.perf_eval = True
            if self.gui.radTrainTest.isChecked():
                self.split_method = 'train_test_split'
                if self.gui.txtTrainSize.text() == '':
                    raise ValueError('Please specify training set size')
                # TODO: check what happens if Train size is 100%
                self.test_size = 1 - int(self.gui.txtTrainSize.text()) / 100
            if self.gui.radCrossVal.isChecked():
                self.split_method = 'kfold'
                if self.gui.txtFolds.text() == '':
                    raise ValueError('Please specify number of folds for cross validation')
                self.kfolds = int(self.gui.txtFolds.text())
        else:
            self.perf_eval = False

    def abort(self, message):
        QMessageBox.critical(self.gui, "Error", message)

    def run_training(self):
        # Starting the procedure of training the model
        try:
            self.check_and_assign()  # check if all user definitions are made
        except ValueError as e:
            self.abort(message=str(e))
            return

        proc = processor.ProcessorMainFunction()  # instance of the Processor main class

        self.prg_widget = self.main.prg_widget
        self.prg_widget.gui.lblCaption_l.setText("Training Machine Learning Model...")
        self.prg_widget.gui.lblCaption_r.setText("Setting up training...")
        self.main.prg_widget.gui.prgBar.setValue(0)
        self.main.prg_widget.gui.setModal(True)
        self.prg_widget.gui.show()

        self.main.qgis_app.processEvents()

        try:
            # Setup everything for training
            proc.train_main.training_setup(lut_metafile=self.lut_path, exclude_bands=self.exclude_bands, npca=self.npca,
                                           model_meta=self.model_meta, para_list=self.para_list,
                                           noisetype=self.noisetype, noiselevel=self.noiselevel,
                                           algorithm=self.algorithm, use_al=self.use_al, use_insitu=self.use_insitu,
                                           perf_eval=self.perf_eval,
                                           split_method=self.split_method, kfolds=self.kfolds,
                                           n_initial=self.n_initial, test_size=self.test_size)
        except ValueError as e:
            self.abort(message="Failed to setup model training: {}".format(str(e)))
            self.prg_widget.gui.lblCancel.setText("")
            self.prg_widget.gui.allow_cancel = True
            self.prg_widget.gui.close()
            return

        # if new models are added, change the text of the ProgressBar accordingly
        self.prg_widget.gui.lblCaption_r.setText("Starting training of MLRA...")
        self.main.qgis_app.processEvents()

        # TODO: uncomment lines here
        # try:
        #     # Train model and dump it to memory
        proc.train_main.train_and_dump(prgbar_widget=self.prg_widget, qgis_app=self.main.qgis_app)
        # except ValueError as e:
        #     self.abort(message="Failed to train model: {}".format(str(e)))
        #     self.prg_widget.gui.lblCancel.setText("")
        #     self.prg_widget.gui.allow_cancel = True
        #     self.prg_widget.gui.close()
        #     return
        self.results_dict = proc.train_main.get_result_dict()

        self.prg_widget.gui.lblCancel.setText("")
        self.prg_widget.gui.allow_cancel = True
        self.prg_widget.gui.close()
        QMessageBox.information(self.gui, "Finish", "Training finished")
        #▬self.gui.close()
        if self.perf_eval:
            self.perfView_widget = self.main.performance_view
            self.perfView_widget.collect(self.results_dict)
            self.perfView_widget.gui.show()


class perfView:
    def __init__(self, main):
        self.main = main
        self.gui = Performance_GUI()
        self.connections()
        self.all_results_dict = None

        self.layout_perf = QVBoxLayout()
        self.gui.perfView.setLayout(self.layout_perf)

        self.figure_perf = Figure(figsize=(6, 6))
        self.canvas_perf = FigureCanvas(self.figure_perf)
        self.toolbar_perf = NavigationToolbar(self.canvas_perf, self.gui.scatterView)
        self.layout_perf.addWidget(self.canvas_perf)
        self.layout_perf.addWidget(self.toolbar_perf)

        self.layout_scatter = QVBoxLayout()
        self.gui.scatterView.setLayout(self.layout_scatter)

        self.figure_scatter = Figure(figsize=(6, 6))
        self.canvas_scatter = FigureCanvas(self.figure_scatter)
        self.toolbar_scatter = NavigationToolbar(self.canvas_scatter, self.gui.scatterView)
        self.layout_scatter.addWidget(self.canvas_scatter)
        self.layout_scatter.addWidget(self.toolbar_scatter)

    def connections(self):
        self.gui.cmdQuit.clicked.connect(lambda: self.gui.close())
        self.gui.modelComboBox.currentIndexChanged.connect(self.plot_results)

    def collect(self, dict):
        self.all_results_dict = dict
        for key in dict:
            self.gui.modelComboBox.addItem(str(key))

    def close(self):
        pass

    def plot_results(self, index):
        key = self.gui.modelComboBox.itemText(index)  # Get the text of the selected item
        data = self.all_results_dict.get(key, None)  # Retrieve the data from the dictionary

        # def colorbar(mappable):
        #     ax = mappable.axes
        #     fig = ax.figure
        #     divider = make_axes_locatable(ax)
        #     cax = divider.append_axes("right", size="5%", pad=0.05)
        #     return fig.colorbar(mappable, cax=cax)
        def format_float_by_scale(value):
            if value >= 100:
                formatted_value = "{:.0f}".format(value)
            elif value >= 10:
                formatted_value = "{:.1f}".format(value)
            elif value >= 1:
                formatted_value = "{:.2f}".format(value)
            elif value >= 0.1:
                formatted_value = "{:.3f}".format(value)
            else:
                formatted_value = "{:.4f}".format(value)
            return formatted_value

        if data is None:
            return

        performances, y_val, predictions = data["performances"], data["y_val"], data["predictions"]
        if isinstance(performances, np.ndarray):
            performances = [performances]
        performances = np.asarray(performances).flatten()
        y_val = np.asarray(y_val).flatten()
        final_pred = np.asarray(predictions).flatten()

        pred_std = None
        try:
            pred_std = np.asarray(data["stds"]).flatten()
        except:
            pred_std = np.empty((0,))

        r2 = r2_score(y_val, final_pred)

        self.figure_perf.clf()
        self.figure_scatter.clf()
        # Create a new subplot
        ax = self.figure_perf.add_subplot(111)
        if isinstance(performances, np.ndarray) and len(performances) > 1:
            # Plot the data
            ax.plot(range(len(performances)), performances, 'k-')
            ax.set_xlabel('Number of added samples')
            ax.set_ylabel('RMSE {}'.format(key))
            ax.tick_params("both")
            # Redraw the canvas
        else:
            performance = [format_float_by_scale(i) for i in performances]
            ax.text(0.5, 0.5,
                    'No Active Learning applied\nFull test set RMSE = ' + str(np.array(performance[0], dtype=float)),
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        self.canvas_perf.draw()


        # Create a new subplot
        ax0 = self.figure_scatter.add_subplot(111, aspect='equal')
        # Scatter plot
        if not isinstance(pred_std, np.ndarray):
            pred_std = np.array(pred_std)
        if pred_std.size > 0:
            scatter = ax0.scatter(y_val, final_pred, c=pred_std, cmap='plasma')
        else:
            scatter = ax0.scatter(y_val, final_pred, c='k')
        # 1:1 line
        ax_max = max(y_val.max(), final_pred.max())
        ax0.plot([0, ax_max], [0, ax_max], 'k-')
        # Regression line
        lr = LinearRegression()
        lr.fit(y_val.reshape(-1, 1), final_pred)
        x_fit = np.linspace(0, ax_max, 100)
        y_fit = lr.predict(x_fit.reshape(-1, 1))
        ax0.plot(x_fit, y_fit, 'r-')

        ax0.text(0.05, 0.95, 'R² = {:.2f}'.format(r2), transform=ax0.transAxes)
        ax0.set_xlabel('{} measured'.format(key))
        ax0.set_ylabel('{} estimated'.format(key))
        ax0.tick_params("both")

        # Colorbar.
        if pred_std.size > 0:
            the_divider = make_axes_locatable(ax0)
            color_axis = the_divider.append_axes("right", size="5%", pad=0.1)
            scatter = ax0.scatter(y_val, final_pred, c=pred_std, cmap='plasma')
            cbar = plt.colorbar(scatter, cax=color_axis)
            cbar.set_label(label='SD', labelpad=0)

        # Redraw the canvas
        self.canvas_scatter.draw()

# The SelectWavelengths class allows to add/remove wavelengths from the inversion
class SelectWavelengths:
    def __init__(self, main):
        self.main = main
        self.gui = SelectWavelengthsGUI()
        self.connections()

    def connections(self):
        self.gui.cmdSendExclude.clicked.connect(lambda: self.send(direction="in_to_ex"))
        self.gui.cmdSendInclude.clicked.connect(lambda: self.send(direction="ex_to_in"))
        self.gui.cmdAll.clicked.connect(lambda: self.select(select="all"))
        self.gui.cmdNone.clicked.connect(lambda: self.select(select="none"))
        self.gui.cmdCancel.clicked.connect(lambda: self.gui.close())
        self.gui.cmdOK.clicked.connect(lambda: self.ok())

    def populate(self, default_exclude):
        if self.main.ann_training.nbands < 10:
            width = 1
        elif self.main.ann_training.nbands < 100:
            width = 2
        elif self.main.ann_training.nbands < 1000:
            width = 3
        else:
            width = 4

        # Any bands with central wavelengths in the specified domain are excluded by default,
        # i.e. the GUI is prepared to add these to the exclude list;
        for i in range(self.main.ann_training.nbands):
            if i in default_exclude:
                str_band_no = '{num:0{width}}'.format(num=i + 1, width=width)
                label = "band %s: %6.2f %s" % (str_band_no, self.main.ann_training.wl[i], self.main.ann_training.wunit)
                self.gui.lstExcluded.addItem(label)
            else:
                str_band_no = '{num:0{width}}'.format(num=i+1, width=width)
                label = "band %s: %6.2f %s" % (str_band_no, self.main.ann_training.wl[i], self.main.ann_training.wunit)
                self.gui.lstIncluded.addItem(label)

    def send(self, direction):
        # Send wavelengths to the include or the exclude list (the function handles both, the direction is passed)
        if direction == "in_to_ex":
            origin = self.gui.lstIncluded
            destination = self.gui.lstExcluded
        elif direction == "ex_to_in":
            origin = self.gui.lstExcluded
            destination = self.gui.lstIncluded
        else:
            return

        for item in origin.selectedItems():
            # move the selected Items from the origin list to the destination list
            index = origin.indexFromItem(item).row()
            destination.addItem(origin.takeItem(index))

        # re-sort the items in both lists (items were added at the bottom)
        origin.sortItems()
        destination.sortItems()
        self.gui.setDisabled(False)

    def select(self, select):
        self.gui.setDisabled(True)
        if select == "all":
            self.gui.lstIncluded.selectAll()
            self.gui.lstExcluded.clearSelection()
            self.send(direction="in_to_ex")
        elif select == "none":
            self.gui.lstExcluded.selectAll()
            self.gui.lstIncluded.clearSelection()
            self.send(direction="ex_to_in")
        else:
            return

    def ok(self):
        list_object = self.gui.lstExcluded
        raw_list = []
        for i in range(list_object.count()):  # read from the QtObect "list" all items as text
            item = list_object.item(i).text()
            raw_list.append(item)

        # convert the text-string of the list object into a python list of integers (bands to be excluded)
        self.main.ann_training.exclude_bands = [int(raw_list[i].split(" ")[1][:-1])-1 for i in range(len(raw_list))]
        self.main.ann_training.nbands_valid = self.main.ann_training.nbands - len(self.main.ann_training.exclude_bands)

        # Join the list to a string and set it to the txtExclude lineEdit
        exclude_string = " ".join(str(x+1) for x in self.main.ann_training.exclude_bands)
        self.main.ann_training.gui.txtExclude.setText(exclude_string)

        # clean up
        for list_object in [self.gui.lstIncluded, self.gui.lstExcluded]:
            list_object.clear()

        self.gui.close()


# class PRG handles the GUI of the ProgressBar
class PRG:
    def __init__(self, main):
        self.main = main
        self.gui = PRG_GUI()
        self.gui.lblCancel.setVisible(False)
        self.connections()

    def connections(self):
        self.gui.cmdCancel.clicked.connect(lambda: self.cancel())

    def cancel(self):
        self.gui.allow_cancel = True
        self.gui.cmdCancel.setDisabled(True)
        self.gui.lblCancel.setText("-1")


# class MainUiFunc is the interface between all sub-GUIs, so they can communicate between each other
class MainUiFunc:
    def __init__(self):
        self.qgis_app = QApplication.instance()
        self.ann_training = ML_Training(self)
        self.select_wavelengths = SelectWavelengths(self)
        self.prg_widget = PRG(self)
        self.performance_view = perfView(self)

    def show(self):
        self.ann_training.gui.show()

    def pass_results(self):
        pass

if __name__ == '__main__':
    from enmapbox.testing import start_app
    app = start_app()
    m = MainUiFunc()
    m.show()
    lut_path = r"E:\LUTs\testLUT_2000_00meta.lut"
    m.ann_training.open_lut(lutpath=lut_path)
    m.ann_training.get_folder(path="E:\LUTs\Model_TEST/")
    sys.exit(app.exec_())
