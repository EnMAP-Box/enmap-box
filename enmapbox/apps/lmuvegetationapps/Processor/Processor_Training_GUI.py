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
#ensure to call QGIS before PyQtGraph
from qgis.PyQt.QtWidgets import *
import lmuvegetationapps.Processor.Processor_Inversion_core as processor
from lmuvegetationapps import APP_DIR
from _classic.hubflow.core import *

from enmapbox.gui.utils import loadUi

pathUI_train = os.path.join(APP_DIR, 'Resources/UserInterfaces/Processor_Train.ui')
pathUI_wavelength = os.path.join(APP_DIR, 'Resources/UserInterfaces/Select_Wavelengths.ui')
pathUI_prgbar = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')


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

# MLTraining is a GUI handler for training new ML-models. For more information, go to Processor_Inversion_core.py
class ML_Training:
    def __init__(self, main):
        self.main = main
        self.gui = MLTrainingGUI()
        self.initial_values()
        self.connections()

    def initial_values(self):
        # exclude_wavelengths: from ... to [nm]; these are default values for atmospheric water vapor absorption
        self.exclude_wavelengths = [[1290, 1525], [1730, 1970], [2450, 2500]]
        self.lut_path = None  # file path to the LUT metafile
        self.meta_dict = None  # intial empty dictionary for LUT meta
        self.wunit = "nanometers"
        self.wl, self.nbands, self.nbands_valid = (None, None, None)
        self.out_dir = None  # directory for output
        self.model_name = None  # name of the output model

    def connections(self):
        self.gui.cmdInputLUT.clicked.connect(lambda: self.open_lut())
        self.gui.cmdModelDir.clicked.connect(lambda: self.get_folder())
        self.gui.cmdRun.clicked.connect(lambda: self.run_training())
        self.gui.cmdClose.clicked.connect(lambda: self.gui.close())

        self.gui.cmdExcludeBands.clicked.connect(lambda: self.open_wavelength_selection())
        self.gui.cmbPCA.toggled.connect(lambda: self.handle_pca())

    def open_lut(self):  # open and read a lut-metafile
        result = str(QFileDialog.getOpenFileName(caption='Select LUT meta-file', filter="LUT-file (*.lut)")[0])
        if not result:
            return
        self.lut_path = result
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
        self.wl = np.asarray(self.meta_dict['wavelengths']).astype(np.float16)
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
        self.gui.cmbPCA.setEnabled(True)
        self.gui.cmbPCA.setChecked(True)

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
                self.npca = 15
            self.gui.spnPCA.setValue(self.npca)  # place the value in the spinBox of the GUI
        if not self.gui.cmbPCA.isChecked():
            self.gui.spnPCA.setDisabled(True)
            self.npca = 0

    def get_folder(self):
        # The model folder is important, as it contains all files needed
        path = str(QFileDialog.getExistingDirectory(caption='Select Output Directory for Model'))
        if path:
            self.gui.txtModelDir.setText(path)
            self.out_dir = self.gui.txtModelDir.text().replace("\\", "/")
            if not self.out_dir[-1] == "/":  # last letter of the folder name needs to be a slash to add filenames
                self.out_dir += "/"

    def check_and_assign(self):
        if not self.lut_path:
            raise ValueError("A Lookup-Table metafile needs to be selected!")
        if not os.path.isdir(self.out_dir):
            raise ValueError("Output directory does not exist!")
        if self.gui.txtModelName.text() == "":
            raise ValueError("Please specify a name for the model")
        else:
            self.model_name = self.gui.txtModelName.text()
            self.model_meta = self.out_dir + self.model_name + '.meta'

        if self.gui.spnPCA.isEnabled():
            self.npca = self.gui.spnPCA.value()
            if self.npca > self.nbands_valid:
                raise ValueError("Model cannot be trained with {:d} components if LUT has only {:d} "
                                 "bands ({:d} minus {:d} excluded)".format(self.npca, self.nbands_valid, self.nbands,
                                                                           len(self.exclude_bands)))
        else:
            self.npca = 0

    def abort(self, message):
        QMessageBox.critical(self.gui, "Error", message)

    def run_training(self):
        # Starting the procedure of training the model
        try:
            self.check_and_assign()  # check if all user definitions are made
        except ValueError as e:
            self.abort(message=str(e))
            return

        self.prg_widget = self.main.prg_widget
        self.prg_widget.gui.lblCaption_l.setText("Training Machine Learning Model")
        self.prg_widget.gui.lblCaption_r.setText("Setting up training...")
        self.main.prg_widget.gui.prgBar.setValue(0)
        self.main.prg_widget.gui.setModal(True)
        self.prg_widget.gui.show()

        self.main.qgis_app.processEvents()

        proc = processor.ProcessorMainFunction()  # instance of the Processor main class

        try:
            # Setup everything for training
            proc.train_main.training_setup(lut_metafile=self.lut_path, exclude_bands=self.exclude_bands, npca=self.npca,
                                           model_meta=self.model_meta)
        except ValueError as e:
            self.abort(message="Failed to setup model training: {}".format(str(e)))
            self.prg_widget.gui.lblCancel.setText("")
            self.prg_widget.gui.allow_cancel = True
            self.prg_widget.gui.close()
            return

        # if new models are added, change the text of the ProgressBar accordingly
        self.prg_widget.gui.lblCaption_r.setText("Starting training of Neural Network...")
        self.main.qgis_app.processEvents()

        try:
            # Train model and dump it to memory
            proc.train_main.train_and_dump(prgbar_widget=self.prg_widget, qgis_app=self.main.qgis_app)
        except ValueError as e:
            self.abort(message="Failed to train model: {}".format(str(e)))
            self.prg_widget.gui.lblCancel.setText("")
            self.prg_widget.gui.allow_cancel = True
            self.prg_widget.gui.close()
            return

        self.prg_widget.gui.lblCancel.setText("")
        self.prg_widget.gui.allow_cancel = True
        self.prg_widget.gui.close()
        QMessageBox.information(self.gui, "Finish", "Training finished")
        self.gui.close()


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

    def show(self):
        self.ann_training.gui.show()


if __name__ == '__main__':
    from enmapbox.testing import start_app
    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())
