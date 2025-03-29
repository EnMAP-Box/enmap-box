# -*- coding: utf-8 -*-
"""
***************************************************************************
    CreateLUT_GUI.py - LMU Agri Apps - interactive creation of PROSAIL/PROINFORM look-up-tables - GUI
    -----------------------------------------------------------------------
    begin                : 05/2018
    copyright            : (C) 2018 Martin Danner; Matthias Wocher
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
    along with this software. If not, see <https://www.gnu.org/licenses/>.
***************************************************************************
"""

# Fills and handles the GUI for creating LUTs in the EnMAP-Box

import sys
import os
import numpy as np
from scipy.interpolate import interp1d

from qgis.gui import *
# ensure to call QGIS before PyQtGraph
from enmapbox.qgispluginsupport.qps.pyqtgraph import pyqtgraph as pg

from qgis.PyQt.QtWidgets import *
import lmuvegetationapps.Resources.PROSAIL.call_model as mod
from lmuvegetationapps.Resources.Spec2Sensor.Spec2Sensor_core import Spec2Sensor, BuildTrueSRF, BuildGenericSRF
from lmuvegetationapps import APP_DIR
from scipy.stats import norm, uniform
import csv

from qgis.gui import QgsMapLayerComboBox
from _classic.hubflow.core import *

from enmapbox.gui.utils import loadUi

pathUI_LUT = os.path.join(APP_DIR, 'Resources/UserInterfaces/CreateLUT.ui')
pathUI2_prgbar = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')
pathUI3_loadtxt = os.path.join(APP_DIR, 'Resources/UserInterfaces/LoadTxtFile.ui')
pathUI4_wavelengths = os.path.join(APP_DIR, 'Resources/UserInterfaces/Select_Wavelengths.ui')
pathUI5_sensor = os.path.join(APP_DIR, 'Resources/UserInterfaces/GUI_SensorEditor.ui')


class LUT_GUI(QDialog):
    def __init__(self, parent=None):
        super(LUT_GUI, self).__init__(parent)
        loadUi(pathUI_LUT, self)


class LoadTxtFileGUI(QDialog):
    def __init__(self, parent=None):
        super(LoadTxtFileGUI, self).__init__(parent)
        loadUi(pathUI3_loadtxt, self)


class SelectWavelengthsGUI(QDialog):
    def __init__(self, parent=None):
        super(SelectWavelengthsGUI, self).__init__(parent)
        loadUi(pathUI4_wavelengths, self)


class SensorEditorGUI(QDialog):
    def __init__(self, parent=None):
        super(SensorEditorGUI, self).__init__(parent)
        loadUi(pathUI5_sensor, self)


class PRG_GUI(QDialog):
    def __init__(self, parent=None):
        super(PRG_GUI, self).__init__(parent)
        loadUi(pathUI2_prgbar, self)
        self.allow_cancel = False

    # Manage the impact of the cancel-button
    def closeEvent(self, event):
        if self.allow_cancel:
            event.accept()
        else:
            event.ignore()


# Class for event filter "Focus lost"
class Filter(QtCore.QObject):
    def __init__(self, gui=None, lut=None):
        super(Filter, self).__init__()
        self.gui = gui
        self.lut = lut

    def bypass(self, widget, event):
        self.eventFilter(widget=widget, event=event)

    def eventFilter(self, widget, event):
        # If the event filter is a "Focus Out" event, then call the Method "assert_inputs_plots"
        # to update GUI and variables
        if event.type() == QtCore.QEvent.FocusOut:
            self.lut.assert_inputs_plot(widget=widget)

        return False  # Do not bother about other events


class LUT:

    def __init__(self, main):
        self.main = main
        self.gui = LUT_GUI()
        self._filter = Filter(gui=self.gui, lut=self)
        self.special_chars()  # place special characters that could not be set in Qt Designer
        self.initial_values()  # Define initial values
        self.dictchecks()  # Create dictionaries for all objects in the GUI
        self.connections()  # Connect buttons (etc) with action

        # self.dict_objects is a dictionary with parameters as keys and all related objects in the GUI stored in lists
        for para in self.dict_objects:
            self.dict_objects[para][0].setChecked(True)  # Object [para][0] is the radio fix button (init. checked)
            self.txt_enables(para=para, mode="fix")
            for obj in range(12):  # all other objects (lineEdits, radio boxes etc.) are set disabled
                self.dict_objects["cp"][obj].setDisabled(True)
                self.dict_objects["cbc"][obj].setDisabled(True)

        self.set_boundaries()  # Define lower and upper limits for variables in the GUI
        self.init_sensorlist()  # Fill the list of sensors to choose from

    def special_chars(self):
        # Set the following special characters (could not be set in Qt Designer)
        self.gui.lblCab.setText('Chlorophyll A + B (Cab) [µg/cm²] \n[0.0 - 100.0]')
        self.gui.lblCm.setText('Dry Matter Content (Cm) [g/cm²] \n[0.0001 - 0.02]')
        self.gui.lblCar.setText('Carotenoids (Ccx) [µg/cm²] \n[0.0 - 30.0]')
        self.gui.lblCanth.setText('Anthocyanins (Canth) [µg/cm²] \n[0.0 - 10.0]')
        self.gui.lblLAI.setText('Leaf Area Index (LAI) [m²/m²] \n[0.01 - 10.0]')
        self.gui.lblLAIu.setText('Undergrowth LAI [m²/m²] \n[0.01 - 10.0]')
        # self.gui.lblCp.setText('Proteins (Cp) [g/cm²] \n[0.0 - 0.01]')
        # self.gui.lblCbc.setText('Carbon-based constit. (CBC) [g/cm²] \n[0.0 - 0.01]')

    def initial_values(self):
        self.typeLIDF = 2
        self.lop = "prospectD"
        self.canopy_arch = "sail"
        self.para_list = [['N', 'cab', 'cw', 'cm', 'car', 'cbrown', 'anth', 'cp', 'cbc'],
                          ['LAI', 'LIDF', 'hspot', 'tto', 'tts', 'psi', 'psoil'],
                          ['LAIu', 'sd', 'h', 'cd']]  # paras in sublists
        self.para_flat = [item for sublist in self.para_list for item in sublist]  # flat list of para_list
        self.npara_flat = len(self.para_flat)  # number of parameters in total (independent of chosen Prospect)

        self.N, self.cab, self.cw, self.cm, self.car, self.cbrown, self.anth, self.cp, self.cbc, \
            self.LAI, self.LIDF, self.hspot, self.tto, self.tts, self.psi, self.psoil, self.LAIu, self.sd, self.h, self.cd \
            = ([] for _ in range(self.npara_flat))  # all parameters are initialized as empty lists

        self.depends = 0  # 0: no dependency of car-cab; 1: dependency is turned on
        self.depends_cp_cbc = 0

        self.path = None
        self.LUT_name = None
        self.sensor = "default"  # "EnMAP", "Sentinel2_Full", "Sentinel2_reduced", "Landsat8" plus others in the dir

        self.ns = None
        self.nlut_total = None
        self.est_time = None
        self.nodat = None
        self.intboost = None
        self.speed = None
        self.bg_spec = None
        self.bg_type = "default"

    def init_sensorlist(self):
        list_dir = os.listdir(APP_DIR + "/Resources/Spec2Sensor/srf")

        # Get all files in the SRF directory
        list_allfiles = [item for item in list_dir if os.path.isfile(APP_DIR + "/Resources/Spec2Sensor/srf/" + item)]

        # Get all files from that list with extension .srf, but pop the extension to get the name of the sensor
        list_files = [item.split('.')[0] for item in list_allfiles if item.split('.')[1] == 'srf']

        list_files.insert(0, '400-2500 nm @ 1nm')  # Default entry is not read from .srf but written directly
        list_files.append("> Add new sensor...")
        n_sensors = len(list_files)  # How many sensors are available to choose from

        # block all Signals to avoid a trigger when adding/removing sensors from the list
        self.gui.SType_combobox.blockSignals(True)
        self.gui.SType_combobox.clear()
        self.gui.SType_combobox.addItems(list_files)
        self.gui.SType_combobox.blockSignals(False)  # turn the signals back on
        self.gui.lblNoBands.setText('2101')

        # Create a dictionary to map indices of the Dropdown to the files in the folder
        self.sensor_dict = dict(zip(range(n_sensors), list_files))
        self.sensor_dict[0] = 'default'  # rename 0th item, so that s2s knows to not post-process spectra
        self.sensor_dict[n_sensors - 1] = 'addnew'  # rename last item, so that GUI knows to open the sensor-editor

    def dictchecks(self):
        # Some parameters may be enabled or disabled, depending on the RTM used; the app needs to remember the state
        # they were in before they were disabled to restore it when switching back. At first, they are set "off"
        # meaning that their objects are all disabled
        self.dict_checks = {"car": "off", "cbrown": "off", "anth": "off", "cm": "off", "cp": "off", "cbc": "off",
                            "LAIu": "off", "sd": "off", "h": "off", "cd": "off"}

        # Store pointers to the objects in a dictionary to allow iterations
        self.dict_objects = {"N": [self.gui.radio_fix_N, self.gui.radio_gauss_N, self.gui.radio_uni_N,
                                   self.gui.radio_log_N, self.gui.txt_fix_N, self.gui.txt_gauss_min_N,
                                   self.gui.txt_gauss_max_N, self.gui.txt_gauss_mean_N, self.gui.txt_gauss_std_N,
                                   self.gui.txt_log_min_N, self.gui.txt_log_max_N, self.gui.txt_log_steps_N,
                                   self.gui.viewN],
                             "cab": [self.gui.radio_fix_chl, self.gui.radio_gauss_chl, self.gui.radio_uni_chl,
                                     self.gui.radio_log_chl, self.gui.txt_fix_chl, self.gui.txt_gauss_min_chl,
                                     self.gui.txt_gauss_max_chl, self.gui.txt_gauss_mean_chl,
                                     self.gui.txt_gauss_std_chl,
                                     self.gui.txt_log_min_chl, self.gui.txt_log_max_chl, self.gui.txt_log_steps_chl,
                                     self.gui.viewChl],
                             "cw": [self.gui.radio_fix_cw, self.gui.radio_gauss_cw, self.gui.radio_uni_cw,
                                    self.gui.radio_log_cw, self.gui.txt_fix_cw, self.gui.txt_gauss_min_cw,
                                    self.gui.txt_gauss_max_cw, self.gui.txt_gauss_mean_cw, self.gui.txt_gauss_std_cw,
                                    self.gui.txt_log_min_cw, self.gui.txt_log_max_cw, self.gui.txt_log_steps_cw,
                                    self.gui.viewCw],
                             "cm": [self.gui.radio_fix_cm, self.gui.radio_gauss_cm, self.gui.radio_uni_cm,
                                    self.gui.radio_log_cm, self.gui.txt_fix_cm, self.gui.txt_gauss_min_cm,
                                    self.gui.txt_gauss_max_cm, self.gui.txt_gauss_mean_cm, self.gui.txt_gauss_std_cm,
                                    self.gui.txt_log_min_cm, self.gui.txt_log_max_cm, self.gui.txt_log_steps_cm,
                                    self.gui.viewCm],
                             "car": [self.gui.radio_fix_car, self.gui.radio_gauss_car, self.gui.radio_uni_car,
                                     self.gui.radio_log_car, self.gui.txt_fix_car, self.gui.txt_gauss_min_car,
                                     self.gui.txt_gauss_max_car, self.gui.txt_gauss_mean_car,
                                     self.gui.txt_gauss_std_car,
                                     self.gui.txt_log_min_car, self.gui.txt_log_max_car, self.gui.txt_log_steps_car,
                                     self.gui.viewCar],
                             "cbrown": [self.gui.radio_fix_cbr, self.gui.radio_gauss_cbr, self.gui.radio_uni_cbr,
                                        self.gui.radio_log_cbr, self.gui.txt_fix_cbr, self.gui.txt_gauss_min_cbr,
                                        self.gui.txt_gauss_max_cbr, self.gui.txt_gauss_mean_cbr,
                                        self.gui.txt_gauss_std_cbr,
                                        self.gui.txt_log_min_cbr, self.gui.txt_log_max_cbr, self.gui.txt_log_steps_cbr,
                                        self.gui.viewCbr],
                             "anth": [self.gui.radio_fix_canth, self.gui.radio_gauss_canth, self.gui.radio_uni_canth,
                                      self.gui.radio_log_canth, self.gui.txt_fix_canth, self.gui.txt_gauss_min_canth,
                                      self.gui.txt_gauss_max_canth, self.gui.txt_gauss_mean_canth,
                                      self.gui.txt_gauss_std_canth,
                                      self.gui.txt_log_min_canth, self.gui.txt_log_max_canth,
                                      self.gui.txt_log_steps_canth,
                                      self.gui.viewCanth],
                             "cp": [self.gui.radio_fix_cp, self.gui.radio_gauss_cp, self.gui.radio_uni_cp,
                                    self.gui.radio_log_cp, self.gui.txt_fix_cp, self.gui.txt_gauss_min_cp,
                                    self.gui.txt_gauss_max_cp, self.gui.txt_gauss_mean_cp,
                                    self.gui.txt_gauss_std_cp,
                                    self.gui.txt_log_min_cp, self.gui.txt_log_max_cp,
                                    self.gui.txt_log_steps_cp,
                                    self.gui.viewCp],
                             "cbc": [self.gui.radio_fix_cbc, self.gui.radio_gauss_cbc, self.gui.radio_uni_cbc,
                                     self.gui.radio_log_cbc, self.gui.txt_fix_cbc, self.gui.txt_gauss_min_cbc,
                                     self.gui.txt_gauss_max_cbc, self.gui.txt_gauss_mean_cbc,
                                     self.gui.txt_gauss_std_cbc,
                                     self.gui.txt_log_min_cbc, self.gui.txt_log_max_cbc,
                                     self.gui.txt_log_steps_cbc,
                                     self.gui.viewCbc],
                             "LAI": [self.gui.radio_fix_lai, self.gui.radio_gauss_lai, self.gui.radio_uni_lai,
                                     self.gui.radio_log_lai, self.gui.txt_fix_lai, self.gui.txt_gauss_min_lai,
                                     self.gui.txt_gauss_max_lai, self.gui.txt_gauss_mean_lai,
                                     self.gui.txt_gauss_std_lai,
                                     self.gui.txt_log_min_lai, self.gui.txt_log_max_lai, self.gui.txt_log_steps_lai,
                                     self.gui.viewLAI],
                             "LIDF": [self.gui.radio_fix_alia, self.gui.radio_gauss_alia, self.gui.radio_uni_alia,
                                      self.gui.radio_log_alia, self.gui.txt_fix_alia, self.gui.txt_gauss_min_alia,
                                      self.gui.txt_gauss_max_alia, self.gui.txt_gauss_mean_alia,
                                      self.gui.txt_gauss_std_alia,
                                      self.gui.txt_log_min_alia, self.gui.txt_log_max_alia, self.gui.txt_log_steps_alia,
                                      self.gui.viewALIA],
                             "hspot": [self.gui.radio_fix_hspot, self.gui.radio_gauss_hspot, self.gui.radio_uni_hspot,
                                       self.gui.radio_log_hspot, self.gui.txt_fix_hspot, self.gui.txt_gauss_min_hspot,
                                       self.gui.txt_gauss_max_hspot, self.gui.txt_gauss_mean_hspot,
                                       self.gui.txt_gauss_std_hspot,
                                       self.gui.txt_log_min_hspot, self.gui.txt_log_max_hspot,
                                       self.gui.txt_log_steps_hspot,
                                       self.gui.viewHspot],
                             "tto": [self.gui.radio_fix_oza, self.gui.radio_gauss_oza, self.gui.radio_uni_oza,
                                     self.gui.radio_log_oza, self.gui.txt_fix_oza, self.gui.txt_gauss_min_oza,
                                     self.gui.txt_gauss_max_oza, self.gui.txt_gauss_mean_oza,
                                     self.gui.txt_gauss_std_oza,
                                     self.gui.txt_log_min_oza, self.gui.txt_log_max_oza, self.gui.txt_log_steps_oza,
                                     self.gui.viewOZA],
                             "tts": [self.gui.radio_fix_sza, self.gui.radio_gauss_sza, self.gui.radio_uni_sza,
                                     self.gui.radio_log_sza, self.gui.txt_fix_sza, self.gui.txt_gauss_min_sza,
                                     self.gui.txt_gauss_max_sza, self.gui.txt_gauss_mean_sza,
                                     self.gui.txt_gauss_std_sza,
                                     self.gui.txt_log_min_sza, self.gui.txt_log_max_sza, self.gui.txt_log_steps_sza,
                                     self.gui.viewSZA],
                             "psi": [self.gui.radio_fix_raa, self.gui.radio_gauss_raa, self.gui.radio_uni_raa,
                                     self.gui.radio_log_raa, self.gui.txt_fix_raa, self.gui.txt_gauss_min_raa,
                                     self.gui.txt_gauss_max_raa, self.gui.txt_gauss_mean_raa,
                                     self.gui.txt_gauss_std_raa,
                                     self.gui.txt_log_min_raa, self.gui.txt_log_max_raa, self.gui.txt_log_steps_raa,
                                     self.gui.viewRAA],
                             "psoil": [self.gui.radio_fix_psoil, self.gui.radio_gauss_psoil, self.gui.radio_uni_psoil,
                                       self.gui.radio_log_psoil, self.gui.txt_fix_psoil, self.gui.txt_gauss_min_psoil,
                                       self.gui.txt_gauss_max_psoil, self.gui.txt_gauss_mean_psoil,
                                       self.gui.txt_gauss_std_psoil,
                                       self.gui.txt_log_min_psoil, self.gui.txt_log_max_psoil,
                                       self.gui.txt_log_steps_psoil,
                                       self.gui.viewPsoil],
                             "LAIu": [self.gui.radio_fix_laiu, self.gui.radio_gauss_laiu, self.gui.radio_uni_laiu,
                                      self.gui.radio_log_laiu, self.gui.txt_fix_laiu, self.gui.txt_gauss_min_laiu,
                                      self.gui.txt_gauss_max_laiu, self.gui.txt_gauss_mean_laiu,
                                      self.gui.txt_gauss_std_laiu,
                                      self.gui.txt_log_min_laiu, self.gui.txt_log_max_laiu, self.gui.txt_log_steps_laiu,
                                      self.gui.viewLAIu],
                             "sd": [self.gui.radio_fix_sd, self.gui.radio_gauss_sd, self.gui.radio_uni_sd,
                                    self.gui.radio_log_sd, self.gui.txt_fix_sd, self.gui.txt_gauss_min_sd,
                                    self.gui.txt_gauss_max_sd, self.gui.txt_gauss_mean_sd, self.gui.txt_gauss_std_sd,
                                    self.gui.txt_log_min_sd, self.gui.txt_log_max_sd, self.gui.txt_log_steps_sd,
                                    self.gui.viewSD],
                             "h": [self.gui.radio_fix_h, self.gui.radio_gauss_h, self.gui.radio_uni_h,
                                   self.gui.radio_log_h, self.gui.txt_fix_h, self.gui.txt_gauss_min_h,
                                   self.gui.txt_gauss_max_h, self.gui.txt_gauss_mean_h, self.gui.txt_gauss_std_h,
                                   self.gui.txt_log_min_h, self.gui.txt_log_max_h, self.gui.txt_log_steps_h,
                                   self.gui.viewH],
                             "cd": [self.gui.radio_fix_cd, self.gui.radio_gauss_cd, self.gui.radio_uni_cd,
                                    self.gui.radio_log_cd, self.gui.txt_fix_cd, self.gui.txt_gauss_min_cd,
                                    self.gui.txt_gauss_max_cd, self.gui.txt_gauss_mean_cd, self.gui.txt_gauss_std_cd,
                                    self.gui.txt_log_min_cd, self.gui.txt_log_max_cd, self.gui.txt_log_steps_cd,
                                    self.gui.viewCD]}

    def connections(self):
        # Sensor Type (Dropdown)
        self.gui.SType_combobox.currentIndexChanged. \
            connect(lambda: self.select_s2s(sensor_index=self.gui.SType_combobox.currentIndex()))

        # Models
        self.gui.B_Prospect4.clicked.connect(lambda: self.select_model(lop="prospect4", canopy_arch=self.canopy_arch))
        self.gui.B_Prospect5.clicked.connect(lambda: self.select_model(lop="prospect5", canopy_arch=self.canopy_arch))
        self.gui.B_Prospect5b.clicked.connect(lambda: self.select_model(lop="prospect5B", canopy_arch=self.canopy_arch))
        self.gui.B_ProspectD.clicked.connect(lambda: self.select_model(lop="prospectD", canopy_arch=self.canopy_arch))
        self.gui.B_ProspectPro.clicked.connect(
            lambda: self.select_model(lop="prospectPro", canopy_arch=self.canopy_arch))

        self.gui.B_LeafModelOnly.clicked.connect(lambda: self.select_model(lop=self.lop, canopy_arch="None"))
        self.gui.B_4Sail.clicked.connect(lambda: self.select_model(lop=self.lop, canopy_arch="sail"))
        self.gui.B_Inform.clicked.connect(lambda: self.select_model(lop=self.lop, canopy_arch="inform"))

        # Select Background
        self.gui.B_DefSoilSpec.clicked.connect(lambda: self.select_background(bg_type="default"))
        self.gui.B_LoadBackSpec.clicked.connect(lambda: self.select_background(bg_type="load"))
        self.gui.B_LoadBackSpec.pressed.connect(lambda: self.select_background(bg_type="load"))
        self.gui.push_SelectFile.clicked.connect(lambda: self.open_file(type="background"))  # load own spectrum

        # Dependencies:
        self.gui.CarCabCheck.stateChanged.connect(lambda: self.init_dependency(which='car_cab'))
        self.gui.CpCBCCheck.stateChanged.connect(lambda: self.init_cp_cbc_dependency())

        # Radio Buttons
        self.gui.radio_fix_N.clicked.connect(lambda: self.txt_enables(para="N", mode="fix"))
        self.gui.radio_gauss_N.clicked.connect(lambda: self.txt_enables(para="N", mode="gauss"))
        self.gui.radio_uni_N.clicked.connect(lambda: self.txt_enables(para="N", mode="uni"))
        self.gui.radio_log_N.clicked.connect(lambda: self.txt_enables(para="N", mode="log"))

        self.gui.radio_fix_chl.clicked.connect(lambda: self.txt_enables(para="cab", mode="fix"))
        self.gui.radio_gauss_chl.clicked.connect(lambda: self.txt_enables(para="cab", mode="gauss"))
        self.gui.radio_uni_chl.clicked.connect(lambda: self.txt_enables(para="cab", mode="uni"))
        self.gui.radio_log_chl.clicked.connect(lambda: self.txt_enables(para="cab", mode="log"))

        self.gui.radio_fix_cw.clicked.connect(lambda: self.txt_enables(para="cw", mode="fix"))
        self.gui.radio_gauss_cw.clicked.connect(lambda: self.txt_enables(para="cw", mode="gauss"))
        self.gui.radio_uni_cw.clicked.connect(lambda: self.txt_enables(para="cw", mode="uni"))
        self.gui.radio_log_cw.clicked.connect(lambda: self.txt_enables(para="cw", mode="log"))

        self.gui.radio_fix_cm.clicked.connect(lambda: self.txt_enables(para="cm", mode="fix"))
        self.gui.radio_gauss_cm.clicked.connect(lambda: self.txt_enables(para="cm", mode="gauss"))
        self.gui.radio_uni_cm.clicked.connect(lambda: self.txt_enables(para="cm", mode="uni"))
        self.gui.radio_log_cm.clicked.connect(lambda: self.txt_enables(para="cm", mode="log"))

        self.gui.radio_fix_car.clicked.connect(lambda: self.txt_enables(para="car", mode="fix"))
        self.gui.radio_gauss_car.clicked.connect(lambda: self.txt_enables(para="car", mode="gauss"))
        self.gui.radio_uni_car.clicked.connect(lambda: self.txt_enables(para="car", mode="uni"))
        self.gui.radio_log_car.clicked.connect(lambda: self.txt_enables(para="car", mode="log"))

        self.gui.radio_fix_canth.clicked.connect(lambda: self.txt_enables(para="anth", mode="fix"))
        self.gui.radio_gauss_canth.clicked.connect(lambda: self.txt_enables(para="anth", mode="gauss"))
        self.gui.radio_uni_canth.clicked.connect(lambda: self.txt_enables(para="anth", mode="uni"))
        self.gui.radio_log_canth.clicked.connect(lambda: self.txt_enables(para="anth", mode="log"))

        self.gui.radio_fix_cp.clicked.connect(lambda: self.txt_enables(para="cp", mode="fix"))
        self.gui.radio_gauss_cp.clicked.connect(lambda: self.txt_enables(para="cp", mode="gauss"))
        self.gui.radio_uni_cp.clicked.connect(lambda: self.txt_enables(para="cp", mode="uni"))
        self.gui.radio_log_cp.clicked.connect(lambda: self.txt_enables(para="cp", mode="log"))

        self.gui.radio_fix_cbc.clicked.connect(lambda: self.txt_enables(para="cbc", mode="fix"))
        self.gui.radio_gauss_cbc.clicked.connect(lambda: self.txt_enables(para="cbc", mode="gauss"))
        self.gui.radio_uni_cbc.clicked.connect(lambda: self.txt_enables(para="cbc", mode="uni"))
        self.gui.radio_log_cbc.clicked.connect(lambda: self.txt_enables(para="cbc", mode="log"))

        self.gui.radio_fix_cbr.clicked.connect(lambda: self.txt_enables(para="cbrown", mode="fix"))
        self.gui.radio_gauss_cbr.clicked.connect(lambda: self.txt_enables(para="cbrown", mode="gauss"))
        self.gui.radio_uni_cbr.clicked.connect(lambda: self.txt_enables(para="cbrown", mode="uni"))
        self.gui.radio_log_cbr.clicked.connect(lambda: self.txt_enables(para="cbrown", mode="log"))

        self.gui.radio_fix_lai.clicked.connect(lambda: self.txt_enables(para="LAI", mode="fix"))
        self.gui.radio_gauss_lai.clicked.connect(lambda: self.txt_enables(para="LAI", mode="gauss"))
        self.gui.radio_uni_lai.clicked.connect(lambda: self.txt_enables(para="LAI", mode="uni"))
        self.gui.radio_log_lai.clicked.connect(lambda: self.txt_enables(para="LAI", mode="log"))

        self.gui.radio_fix_alia.clicked.connect(lambda: self.txt_enables(para="LIDF", mode="fix"))
        self.gui.radio_gauss_alia.clicked.connect(lambda: self.txt_enables(para="LIDF", mode="gauss"))
        self.gui.radio_uni_alia.clicked.connect(lambda: self.txt_enables(para="LIDF", mode="uni"))
        self.gui.radio_log_alia.clicked.connect(lambda: self.txt_enables(para="LIDF", mode="log"))

        self.gui.radio_fix_hspot.clicked.connect(lambda: self.txt_enables(para="hspot", mode="fix"))
        self.gui.radio_gauss_hspot.clicked.connect(lambda: self.txt_enables(para="hspot", mode="gauss"))
        self.gui.radio_uni_hspot.clicked.connect(lambda: self.txt_enables(para="hspot", mode="uni"))
        self.gui.radio_log_hspot.clicked.connect(lambda: self.txt_enables(para="hspot", mode="log"))

        self.gui.radio_fix_oza.clicked.connect(lambda: self.txt_enables(para="tto", mode="fix"))
        self.gui.radio_gauss_oza.clicked.connect(lambda: self.txt_enables(para="tto", mode="gauss"))
        self.gui.radio_uni_oza.clicked.connect(lambda: self.txt_enables(para="tto", mode="uni"))
        self.gui.radio_log_oza.clicked.connect(lambda: self.txt_enables(para="tto", mode="log"))

        self.gui.radio_fix_sza.clicked.connect(lambda: self.txt_enables(para="tts", mode="fix"))
        self.gui.radio_gauss_sza.clicked.connect(lambda: self.txt_enables(para="tts", mode="gauss"))
        self.gui.radio_uni_sza.clicked.connect(lambda: self.txt_enables(para="tts", mode="uni"))
        self.gui.radio_log_sza.clicked.connect(lambda: self.txt_enables(para="tts", mode="log"))

        self.gui.radio_fix_raa.clicked.connect(lambda: self.txt_enables(para="psi", mode="fix"))
        self.gui.radio_gauss_raa.clicked.connect(lambda: self.txt_enables(para="psi", mode="gauss"))
        self.gui.radio_uni_raa.clicked.connect(lambda: self.txt_enables(para="psi", mode="uni"))
        self.gui.radio_log_raa.clicked.connect(lambda: self.txt_enables(para="psi", mode="log"))

        self.gui.radio_fix_psoil.clicked.connect(lambda: self.txt_enables(para="psoil", mode="fix"))
        self.gui.radio_gauss_psoil.clicked.connect(lambda: self.txt_enables(para="psoil", mode="gauss"))
        self.gui.radio_uni_psoil.clicked.connect(lambda: self.txt_enables(para="psoil", mode="uni"))
        self.gui.radio_log_psoil.clicked.connect(lambda: self.txt_enables(para="psoil", mode="log"))

        self.gui.radio_fix_sd.clicked.connect(lambda: self.txt_enables(para="sd", mode="fix"))
        self.gui.radio_gauss_sd.clicked.connect(lambda: self.txt_enables(para="sd", mode="gauss"))
        self.gui.radio_uni_sd.clicked.connect(lambda: self.txt_enables(para="sd", mode="uni"))
        self.gui.radio_log_sd.clicked.connect(lambda: self.txt_enables(para="sd", mode="log"))

        self.gui.radio_fix_laiu.clicked.connect(lambda: self.txt_enables(para="LAIu", mode="fix"))
        self.gui.radio_gauss_laiu.clicked.connect(lambda: self.txt_enables(para="LAIu", mode="gauss"))
        self.gui.radio_uni_laiu.clicked.connect(lambda: self.txt_enables(para="LAIu", mode="uni"))
        self.gui.radio_log_laiu.clicked.connect(lambda: self.txt_enables(para="LAIu", mode="log"))

        self.gui.radio_fix_h.clicked.connect(lambda: self.txt_enables(para="h", mode="fix"))
        self.gui.radio_gauss_h.clicked.connect(lambda: self.txt_enables(para="h", mode="gauss"))
        self.gui.radio_uni_h.clicked.connect(lambda: self.txt_enables(para="h", mode="uni"))
        self.gui.radio_log_h.clicked.connect(lambda: self.txt_enables(para="h", mode="log"))

        self.gui.radio_fix_cd.clicked.connect(lambda: self.txt_enables(para="cd", mode="fix"))
        self.gui.radio_gauss_cd.clicked.connect(lambda: self.txt_enables(para="cd", mode="gauss"))
        self.gui.radio_uni_cd.clicked.connect(lambda: self.txt_enables(para="cd", mode="uni"))
        self.gui.radio_log_cd.clicked.connect(lambda: self.txt_enables(para="cd", mode="log"))

        # Buttons
        self.gui.cmdRun.clicked.connect(lambda: self.run_LUT())
        self.gui.cmdClose.clicked.connect(lambda: self.gui.close())
        self.gui.cmdOpenFolder.clicked.connect(lambda: self.get_folder())
        self.gui.cmdLUTcalc.clicked.connect(lambda: self.get_lutsize())
        self.gui.cmdImport.clicked.connect(lambda: self.import_paras())
        # self.gui.cmdPlot.clicked.connect(lambda: self.plot_para())

        # Focus Out (Line Edits)
        for para in self.dict_objects:
            for i in range(4, 12):  # 4: fixed; 5-8: min, max, mean, std; 9-11: logical min, max, step
                self.dict_objects[para][i].installEventFilter(self._filter)

    def txt_enables(self, para, mode):
        # manages the enabling and disabling of lineEdits depending on the enabled radioButtons
        # mode may also be "off". In this case nothing happens
        if mode == "fix":
            self.dict_objects[para][4].setEnabled(True)
            for i in range(5, 12):
                self.dict_objects[para][i].setEnabled(False)
                self.dict_objects[para][i].setText("")

        elif mode == "gauss":
            for i in [4, 9, 10, 11]:
                self.dict_objects[para][i].setEnabled(False)
                self.dict_objects[para][i].setText("")
            for i in range(5, 9):
                self.dict_objects[para][i].setEnabled(True)

        elif mode == "uni":
            for i in [4, 7, 8, 9, 10, 11]:
                self.dict_objects[para][i].setEnabled(False)
                self.dict_objects[para][i].setText("")
            self.dict_objects[para][5].setEnabled(True)
            self.dict_objects[para][6].setEnabled(True)

        elif mode == "log":
            for i in range(4, 9):
                self.dict_objects[para][i].setEnabled(False)
                self.dict_objects[para][i].setText("")
            for i in [9, 10, 11]:
                self.dict_objects[para][i].setEnabled(True)

        # remember the state of those parameters which can be switched off for some RTMs
        if para in self.dict_checks:
            self.dict_checks[para] = mode

    def assert_inputs_plot(self, widget=None, para=None):
        # This is called as "FocusOut event", so that entered parameter values need not be confirmed via Return key
        # It is alternatively called when importing parameters from file

        # if no para is passed (FocusOut-Event), find the parameter that triggered the call
        # if para is provided, then it's the "Import" method which knows the parameter
        if para is None:  # if no para is passed (FocusOut-Event)
            for pp in self.dict_objects:  # browse through all parameters
                if widget in self.dict_objects[pp]:
                    # when widget (that called the event) is found in the para objects, then cancel the search and keep para
                    para = pp
                    break

        if self.dict_objects[para][0].isChecked():  # fix
            try:
                vals = [float(self.dict_objects[para][4].text())]  # needs to be of type "list"
                # (even single values)
                ns = self.gui.spinNS.value()
                bar = pg.BarGraphItem(x=vals, height=ns, width=0.01)
                self.dict_objects[para][12].addItem(bar)
                self.dict_objects[para][12].plot(clear=True)

            except ValueError as e:
                print(str(e))

        elif self.dict_objects[para][1].isChecked():  # gauss
            try:
                vals = [float(self.dict_objects[para][i].text()) for i in [5, 6, 7, 8]]
                xIncr = (vals[1] - vals[0]) / 100.0
                xVals = np.arange(vals[0], vals[1], xIncr)
                self.dict_objects[para][12].plot(xVals, norm.pdf(xVals, loc=vals[2], scale=vals[3]),
                                                 clear=True)
            except:
                pass

        elif self.dict_objects[para][2].isChecked():  # uniform
            try:
                vals = [float(self.dict_objects[para][i].text()) for i in [5, 6]]
                xIncr = (vals[1] - vals[0]) / 100.0
                xVals = np.arange(vals[0], vals[1], xIncr)
                self.dict_objects[para][12].plot(xVals, uniform.pdf(xVals, loc=vals[0], scale=vals[1]),
                                                 clear=True)
            except:
                pass

        elif self.dict_objects[para][3].isChecked():  # logical
            try:
                vals = [float(self.dict_objects[para][i].text()) for i in [9, 10, 11]]
                xVals = np.linspace(start=vals[0], stop=vals[1], num=int(vals[2]))
                ns = self.gui.spinNS.value()
                width = (xVals[1] - xVals[0]) / 8
                bar = pg.BarGraphItem(x=xVals, height=ns, width=width)
                self.dict_objects[para][12].addItem(bar)
                self.dict_objects[para][12].plot(clear=True)
                if vals[1] < 1.0:
                    self.dict_objects[para][12].setrange(xVals[0] - width * 2, xVals[-1] + width * 2)
            except:
                pass

        # return False so that the widget will also handle the actual event
        # otherwise it won't focus out
        return False

    def import_paras(self):
        # After creating a LUT, a _00paras.txt file is written with the ranges of the parameters in it
        # The GUI can restore this information and put it into its object - this is useful for creating
        # multiple LUTs with similar settings in a row
        file_choice, _filter = QFileDialog.getOpenFileName(parent=None, caption='Select LUT Parameter Meter File',
                                                           filter="(*00paras.txt)")
        if not file_choice:
            return
        try:
            with open(file_choice, 'r') as para_meta:
                metacontent = para_meta.readlines()
                metacontent = [line.rstrip('\n') for line in metacontent]
            name = metacontent[0].split("=")[1]
            lop = metacontent[1].split("=")[1]
            canopy_arch = metacontent[2].split("=")[1]
            depends = int(metacontent[3].split("#")[0].split("=")[1])
            para_names = list()
            para_ranges = list()
            para_modes = list()
            for line in range(4, len(metacontent)):
                para_names.append(metacontent[line].split("#")[0].split("=")[0])
                para_range = metacontent[line].split("#")[0].split("=")[1]
                para_range = para_range.replace("[", "").replace("]", "").split(", ")
                para_range = [float(i) for i in para_range]
                para_ranges.append(para_range)
                if len(para_range) == 1:
                    para_modes.append('fix')
                elif len(para_range) == 2:
                    para_modes.append('uni')
                elif len(para_range) == 3:
                    para_modes.append('log')
                elif len(para_range) == 4:
                    para_modes.append('gauss')
                else:
                    raise ValueError
        except:
            self.abort(message="Could not import parameters from file. Please make sure you select an unchanged "
                               "_00paras.txt - file")
            return

        # Check for Car-Cab-Dependency: If it is activated according to the paras-File, set the GUI accordingly
        if depends == 1:
            self.depends = depends
            self.gui.CarCabCheck.setChecked(True)
        else:
            self.depends = 0
            self.gui.CarCabCheck.setChecked(False)
        self.init_dependency(which='car_cab')

        # Check if the LOP and Canopy_arch_model are known and set in the GUI accordingly
        if (lop in ["prospectPro", "prospectD", "prospect5B", "prospect5", "prospect4"]) and \
                (canopy_arch in ["None", "sail", "inform"]):
            self.select_model(lop=lop, canopy_arch=canopy_arch)
            if lop == 'prospectPro':
                self.gui.B_ProspectPro.setChecked(True)
            elif lop == 'prospectD':
                self.gui.B_ProspectD.setChecked(True)
            elif lop == "prospect5B":
                self.gui.B_Prospect5b.setChecked(True)
            elif lop == "prospect5":
                self.gui.B_Prospect5.setChecked(True)
            elif lop == "prospect4":
                self.gui.B_Prospect4.setChecked(True)

            if canopy_arch == "None":
                self.gui.B_LeafModelOnly.setChecked(True)
            elif canopy_arch == "sail":
                self.gui.B_4Sail.setChecked(True)
            elif canopy_arch == "inform":
                self.gui.B_Inform.setChecked(True)

        else:
            return

        for ipara, para in enumerate(para_names):
            if not para == "typeLIDF":  # typeLIDF cannot be changed in this GUI
                if para_modes[ipara] == 'fix':
                    self.dict_objects[para][4].setText(str(para_ranges[ipara][0]))  # insert value in "fix" lineEdit
                    which_toggle = 0
                elif para_modes[ipara] == 'gauss':
                    self.dict_objects[para][5].setText(str(para_ranges[ipara][0]))  # min
                    self.dict_objects[para][6].setText(str(para_ranges[ipara][1]))  # max
                    self.dict_objects[para][7].setText(str(para_ranges[ipara][2]))  # mean
                    self.dict_objects[para][8].setText(str(para_ranges[ipara][3]))  # std
                    which_toggle = 1
                elif para_modes[ipara] == 'uni':
                    self.dict_objects[para][5].setText(str(para_ranges[ipara][0]))  # min
                    self.dict_objects[para][6].setText(str(para_ranges[ipara][1]))  # max
                    which_toggle = 2
                elif para_modes[ipara] == 'log':
                    self.dict_objects[para][9].setText(str(para_ranges[ipara][0]))  # logical min
                    self.dict_objects[para][10].setText(str(para_ranges[ipara][1]))  # logical max
                    self.dict_objects[para][11].setText(str(int(para_ranges[ipara][2])))  # logical steps
                    which_toggle = 3
                else:
                    return
                self.dict_objects[para][which_toggle].setChecked(True)  # check the right radioButton
                self.txt_enables(para=para, mode=para_modes[ipara])  # enable all the right lineEdits
                self.assert_inputs_plot(para=para)  # trigger the "focusOut" event manually

    def init_dependency(self, which):
        if which == 'car_cab' and self.depends == 0:
            self.depends = 1
            for obj in range(12):
                self.dict_objects["car"][obj].setDisabled(True)
        else:
            self.depends = 0
            for obj in range(5):
                self.dict_objects["car"][obj].setDisabled(False)

    def init_cp_cbc_dependency(self):
        if self.gui.CpCBCCheck.isChecked():
            self.depends_cp_cbc = 1
        else:
            self.depends_cp_cbc = 0

    def reset_dependency(self):
        self.gui.CarCabCheck.setChecked(False)
        self.depends = 0
        for obj in range(5):
            self.dict_objects["car"][obj].setDisabled(False)

    def set_boundaries(self):
        # min / max allowed
        self.dict_boundaries = {"N": [1.0, 3.0],  # 0
                                "cab": [0.0, 100.0],  # 1
                                "cw": [0.0002, 0.7],  # 2
                                "cm": [0.0001, 0.02],  # 3
                                "car": [0.0, 30.0],  # 4
                                "cbrown": [0.0, 1.0],  # 5
                                "anth": [0.0, 10.0],  # 6
                                "LAI": [0.01, 10.0],  # 7
                                "cp": [0.0, 0.005],  # 8
                                "cbc": [0.0, 0.09],  # 9
                                "LIDF": [0.0, 90.0],  # 10
                                "hspot": [0.0, 1.0],  # 11
                                "tto": [0.0, 89.0],  # 12
                                "tts": [0.0, 89.0],  # 13
                                "psi": [0.0, 180.0],  # 14
                                "psoil": [0.0, 1.0],  # 15 vv forest parameters vv
                                "LAIu": [0.01, 10.0],  # 16
                                "sd": [0.0, 5000.0],  # 17
                                "h": [0.0, 50.0],  # 18
                                "cd": [0.0, 30.0]}  # 19
        # xx ^^ forest parameters ^^

    def select_s2s(self, sensor_index):
        # function is called when a new sensor is chosen from the dropdown
        self.sensor = self.sensor_dict[sensor_index]
        if self.sensor == 'default':
            self.wl = range(400, 2501)
            self.gui.lblNoBands.setText("2101")
            self.gui.spinIntBoost.setValue(1)
        elif self.sensor == 'addnew':  # user chose "add new sensor"
            self.open_sensoreditor()
            return
        else:
            s2s = Spec2Sensor(sensor=self.sensor, nodat=-999)
            sensor_init_success = s2s.init_sensor()
            if not sensor_init_success:
                return
            self.wl = s2s.wl_sensor
            self.gui.spinIntBoost.setValue(10000)
            self.gui.lblNoBands.setText(str(s2s.n_wl_sensor))

    def select_model(self, lop="prospectD", canopy_arch="sail"):
        # function is called when the user picks a different model
        self.lop = lop
        self.reset_dependency()

        if canopy_arch == "None":
            self.canopy_arch = None
            self.gui.BackSpec_label.setEnabled(False)
            self.gui.B_DefSoilSpec.setEnabled(False)
            self.gui.B_LoadBackSpec.setEnabled(False)
            self.gui.grp_canopy.setDisabled(True)
            self.gui.grp_forest.setDisabled(True)

        elif canopy_arch == "sail":
            self.canopy_arch = canopy_arch
            self.gui.lblLAI.setText("Leaf Area Index (LAI) [m2/m2]\n[0.01-10.0]")
            self.gui.grp_canopy.setDisabled(False)
            self.gui.grp_forest.setDisabled(True)
            self.gui.B_Prospect5.setDisabled(False)
            self.gui.B_Prospect4.setDisabled(False)
            self.gui.B_Prospect5b.setDisabled(False)
            self.select_background(bg_type=self.bg_type)

        elif canopy_arch == "inform":
            self.canopy_arch = canopy_arch
            self.gui.lblLAI.setText("Single Tree \nLeaf Area Index (LAI) [m2/m2]\n[0.01-10.0]")
            self.gui.grp_canopy.setDisabled(False)
            self.gui.grp_forest.setDisabled(False)
            self.gui.lblLAIu.setDisabled(False)
            self.select_background(bg_type=self.bg_type)

        if lop == "prospectPro":
            for para in self.para_list[0]:
                for obj in range(4):
                    self.dict_objects[para][obj].setDisabled(False)
            for obj in range(12):
                self.dict_objects["cm"][obj].setDisabled(True)
            self.txt_enables(para="car", mode=self.dict_checks["car"])
            self.txt_enables(para="cbrown", mode=self.dict_checks["cbrown"])
            self.txt_enables(para="anth", mode=self.dict_checks["anth"])
            self.txt_enables(para="cp", mode=self.dict_checks["cp"])
            self.txt_enables(para="cbc", mode=self.dict_checks["cbc"])

        elif lop == "prospectD":
            for para in self.para_list[0]:
                for obj in range(4):
                    self.dict_objects[para][obj].setDisabled(False)
            for obj in range(12):
                self.dict_objects["cp"][obj].setDisabled(True)
                self.dict_objects["cbc"][obj].setDisabled(True)

            self.txt_enables(para="car", mode=self.dict_checks["car"])
            self.txt_enables(para="cbrown", mode=self.dict_checks["cbrown"])
            self.txt_enables(para="anth", mode=self.dict_checks["anth"])
            self.txt_enables(para="cm", mode=self.dict_checks["cm"])

        elif lop == "prospect5B":
            for para in self.para_list[0]:
                for obj in range(4):
                    self.dict_objects[para][obj].setDisabled(False)
            for obj in range(12):
                self.dict_objects["anth"][obj].setDisabled(True)
                self.dict_objects["cp"][obj].setDisabled(True)
                self.dict_objects["cbc"][obj].setDisabled(True)
            self.txt_enables(para="car", mode=self.dict_checks["car"])
            self.txt_enables(para="cbrown", mode=self.dict_checks["cbrown"])
            self.txt_enables(para="cm", mode=self.dict_checks["cm"])

        elif lop == "prospect5":
            for para in self.para_list[0]:
                for obj in range(4):
                    self.dict_objects[para][obj].setDisabled(False)
                for obj in range(12):
                    self.dict_objects["anth"][obj].setDisabled(True)
                    self.dict_objects["cbrown"][obj].setDisabled(True)
                    self.dict_objects["cp"][obj].setDisabled(True)
                    self.dict_objects["cbc"][obj].setDisabled(True)
            self.txt_enables(para="car", mode=self.dict_checks["car"])
            self.txt_enables(para="cm", mode=self.dict_checks["cm"])

        elif lop == "prospect4":
            for para in self.para_list[0]:
                for obj in range(4):
                    self.dict_objects[para][obj].setDisabled(False)
                for obj in range(12):
                    self.dict_objects["anth"][obj].setDisabled(True)
                    self.dict_objects["cbrown"][obj].setDisabled(True)
                    self.dict_objects["car"][obj].setDisabled(True)
                    self.dict_objects["cp"][obj].setDisabled(True)
                    self.dict_objects["cbc"][obj].setDisabled(True)
            self.txt_enables(para="cm", mode=self.dict_checks["cm"])

    def select_background(self, bg_type):
        # function is called when the background type is changed
        self.bg_type = bg_type

        if bg_type == "default":
            self.gui.B_DefSoilSpec.setEnabled(True)
            self.gui.B_LoadBackSpec.setEnabled(True)
            self.gui.push_SelectFile.setEnabled(False)
            self.gui.BackSpec_label.setEnabled(False)
            self.gui.BackSpec_label.setText("")
            self.bg_spec = None  # when bg_spec is None, PROSAIL will use the default soil

            for para in self.para_list[1]:
                for obj in range(4):
                    self.dict_objects[para][obj].setDisabled(False)
            for obj in range(5):
                self.dict_objects["psoil"][obj].setDisabled(False)

        elif bg_type == "load":
            self.gui.B_DefSoilSpec.setEnabled(True)
            self.gui.B_LoadBackSpec.setEnabled(True)
            self.gui.push_SelectFile.setEnabled(True)
            self.gui.push_SelectFile.setText('Select File...')
            self.gui.BackSpec_label.setEnabled(True)

            for para in self.para_list[1]:
                for obj in range(4):
                    self.dict_objects[para][obj].setDisabled(False)
            for obj in range(12):
                self.dict_objects["psoil"][obj].setDisabled(True)

    def get_folder(self):
        # function is called when the user hits "..." to select a dir for the LUT to be stored in
        path = str(QFileDialog.getExistingDirectory(caption='Select Directory for LUT'))
        if path:  # when selecting the dir was successful
            self.gui.lblOutPath.setText(path)
            self.path = self.gui.lblOutPath.text().replace("\\", "/")
            if not self.path[-1] == "/":
                self.path += "/"  # result is to be concatanetd, so the "/" is mandatory

    def get_inputs(self):
        # build empty dictionary for all values selected in the GUI
        self.dict_vals = dict(zip(self.para_flat, ([] for _ in range(self.npara_flat))))

        for para in self.dict_objects:
            for obj in range(4, 12):
                if not self.dict_objects[para][obj].text() == "":
                    try:
                        self.dict_vals[para].append(float(self.dict_objects[para][obj].text()))
                    except ValueError:
                        QMessageBox.critical(self.gui, "Not a number", "'%s' is not a valid number"
                                             % self.dict_objects[para][obj].text())
                        self.dict_vals = dict(zip(self.para_flat, ([] for i in range(self.npara_flat))))  # reset dict
                        return

        self.LUT_name = self.gui.txtLUTname.text()
        self.ns = int(self.gui.spinNS.value())
        self.intboost = int(self.gui.spinIntBoost.value())
        self.nodat = int(self.gui.spinNoData.value())

    def check_inputs(self):
        # check if inputs are valid and respond with errors if values are missing, out of range etc.

        for i, key in enumerate(self.para_list[0]):
            if key == 'car' and self.depends != 0:
                continue  # ignore error of missing values when car is set in dependency to cab

            elif len(self.dict_vals[self.para_list[0][i]]) > 3:  # gauss distribution, out of range?
                if self.dict_vals[self.para_list[0][i]][2] > self.dict_vals[self.para_list[0][i]][1] or \
                        self.dict_vals[self.para_list[0][i]][2] < self.dict_vals[self.para_list[0][i]][0]:
                    self.abort(message='Parameter %s: mean value must lie between min and max' % self.para_list[0][i])
                    return False
                elif self.dict_vals[self.para_list[0][i]][0] < self.dict_boundaries[key][0] or \
                        self.dict_vals[self.para_list[0][i]][1] > self.dict_boundaries[key][1]:
                    self.abort(message='Parameter %s: min / max out of allowed range!' % self.para_list[0][i])
                    return False

            elif len(self.dict_vals[self.para_list[0][i]]) > 1:  # uniform distribution, out of range?
                if self.dict_vals[self.para_list[0][i]][0] < self.dict_boundaries[key][0] or \
                        self.dict_vals[self.para_list[0][i]][1] > self.dict_boundaries[key][1]:
                    self.abort(message='Parameter %s: min / max out of allowed range!' % self.para_list[0][i])
                    return False

            elif len(self.dict_vals[self.para_list[0][i]]) > 0:  # fixed value our of range?
                if self.dict_vals[self.para_list[0][i]][0] < self.dict_boundaries[key][0] or \
                        self.dict_vals[self.para_list[0][i]][0] > self.dict_boundaries[key][1]:
                    self.abort(message='Parameter %s: min / max out of allowed range!' % self.para_list[0][i])
                    return False

        if self.canopy_arch == "sail":
            for i, key in enumerate(self.para_list[1]):
                if key == 'car' and self.depends != 0:
                    continue

                elif len(self.dict_vals[self.para_list[1][i]]) > 3:  # gauss distribution, out of range?
                    if self.dict_vals[self.para_list[1][i]][2] > self.dict_vals[self.para_list[1][i]][1] or \
                            self.dict_vals[self.para_list[1][i]][2] < self.dict_vals[self.para_list[1][i]][0]:
                        self.abort(
                            message='Parameter %s: mean value must lie between min and max' % self.para_list[1][i])
                        return False
                    elif self.dict_vals[self.para_list[1][i]][0] < self.dict_boundaries[key][0] or \
                            self.dict_vals[self.para_list[1][i]][1] > self.dict_boundaries[key][1]:
                        self.abort(message='Parameter %s: min / max out of allowed range!' % self.para_list[1][i])
                        return False

                elif len(self.dict_vals[self.para_list[1][i]]) > 1:  # uniform distribution, out of range?
                    if self.dict_vals[self.para_list[1][i]][0] < self.dict_boundaries[key][0] or \
                            self.dict_vals[self.para_list[1][i]][1] > self.dict_boundaries[key][1]:
                        self.abort(message='Parameter %s: min / max out of allowed range!' % self.para_list[1][i])
                        return False
                elif len(self.dict_vals[self.para_list[1][i]]) > 0:  # fixed value our of range?
                    if self.dict_vals[self.para_list[1][i]][0] < self.dict_boundaries[key][0] or \
                            self.dict_vals[self.para_list[1][i]][0] > self.dict_boundaries[key][1]:
                        self.abort(message='Parameter %s: min / max out of allowed range!' % self.para_list[1][i])
                        return False

        # Check Prospect properties
        if self.lop == "prospectPro":
            if any(len(self.dict_vals[self.para_list[0][i]]) < 1 for i in range(len(self.para_list[0]) - 1)):
                self.abort(message='Leaf Optical Properties parameter(s) missing')
                return False

        elif self.lop == "prospectD":
            if any(len(self.dict_vals[self.para_list[0][i]]) < 1 for i in range(len(self.para_list[0]) - 2)):
                self.abort(message='Leaf Optical Properties parameter(s) missing')
                return False

        elif self.lop == "prospect5B":
            if any(len(self.dict_vals[self.para_list[0][i]]) < 1 for i in range(len(self.para_list[0]) - 3)):
                self.abort(message='Leaf Optical Properties parameter(s) missing')
                return False

        elif self.lop == "prospect5":
            if any(len(self.dict_vals[self.para_list[0][i]]) < 1 for i in range(len(self.para_list[0]) - 4)):
                self.abort(message='Leaf Optical Properties parameter(s) missing')
                return False

        elif self.lop == "prospect4":
            if any(len(self.dict_vals[self.para_list[0][i]]) < 1 for i in range(len(self.para_list[0]) - 5)):
                self.abort(message='Leaf Optical Properties parameter(s) missing')
                return False

        # Check SAIL properties
        if self.canopy_arch == "sail" and self.bg_type == "default":
            if any(len(self.dict_vals[self.para_list[1][i]]) < 1 for i in range(len(self.para_list[1]))):
                self.abort(message='Canopy Architecture parameter(s) missing')
                return False

        if self.canopy_arch == "sail" and self.bg_type == "load":
            if any(len(self.dict_vals[self.para_list[1][i]]) < 1 for i in range(len(self.para_list[1]) - 1)):
                self.abort(message='Canopy Architecture parameter(s) missing')
                return False

        if self.canopy_arch == "inform":
            if any(len(self.dict_vals[self.para_list[2][i]]) < 1 for i in range(len(self.para_list[2]))):
                self.abort(message='Forest Canopy Architecture parameter(s) missing')
                return False

        if not os.path.isdir(self.gui.lblOutPath.text()):
            self.abort(message='Incorrect Path')
            return False

        if self.LUT_name == "" or self.LUT_name is None:
            self.abort(message='Incorrect LUT name')
            return False

        return True

    def get_lutsize(self):
        # Calculate the size of the LUT to be created

        self.get_inputs()
        self.nlut_total = self.ns

        for para in self.dict_vals:
            if len(self.dict_vals[para]) == 3 and any(self.dict_objects[para][i].isEnabled() for i in range(4)):
                self.nlut_total *= self.dict_vals[para][2]

        if self.speed is None:
            self.speedtest()
        time50x = self.speedtest()
        self.speed = time50x * self.nlut_total / 50

        if self.speed > 172800:
            self.gui.lblTimeUnit.setText("days")
            self.speed /= 86400
        elif self.speed > 10800:
            self.gui.lblTimeUnit.setText("hours")
            self.speed /= 3600
        elif self.speed > 120:
            self.gui.lblTimeUnit.setText("min")
            self.speed /= 60
        else:
            self.gui.lblTimeUnit.setText("sec")

        self.gui.lcdNumber.display(self.nlut_total)
        self.gui.lcdSpeed.display(self.speed)

    def speedtest(self):
        # When calculating size and speed of the LUT, this instance is created and timed with dummy input

        model_I = mod.InitModel(lop=self.lop, canopy_arch=self.canopy_arch, nodat=self.nodat,
                                int_boost=self.intboost, s2s=self.sensor)
        time50x = model_I.initialize_vectorized(LUT_dir=None, LUT_name=None, ns=100, tts=[20.0, 60.0], tto=[0.0, 40.0],
                                                psi=[0.0, 180.0], N=[1.1, 2.5], cab=[0.0, 80.0], cw=[0.0002, 0.02],
                                                cm=[0.0001, 0.005], LAI=[0.5, 8.0], LIDF=[10.0, 80.0], typeLIDF=[2],
                                                hspot=[0.1], psoil=[0.5], car=[0.0, 12.0],
                                                cbrown=[0.0, 1.0], anth=[0.0, 10.0], cp=[0.001], cbc=[0.01],
                                                soil=[0.1] * 2101, depends=0, testmode=True)

        return time50x / 2  # It will remain a miracle, why the time is factor 2, but it IS!

    def run_LUT(self):
        # Do the actual work

        self.get_inputs()
        if not self.check_inputs():
            return
        self.get_lutsize()
        self.gui.lcdNumber.display(self.nlut_total)
        self.gui.lcdSpeed.display(self.speed)
        self.main.qgis_app.processEvents()

        self.main.prg_widget.gui.lblCaption_l.setText("Global Inversion")
        self.main.prg_widget.gui.lblCaption_r.setText("Setting up inversion...")
        self.main.prg_widget.gui.prgBar.setValue(0)
        self.main.prg_widget.gui.setModal(True)
        self.main.prg_widget.gui.show()
        self.main.qgis_app.processEvents()

        try:
            # Create an instance of PROSAIL, first initialize
            model_I = mod.InitModel(lop=self.lop, canopy_arch=self.canopy_arch, nodat=self.nodat,
                                    int_boost=self.intboost, s2s=self.sensor)
        except ValueError as e:
            self.abort(message="An error occurred while initializing the LUT: %s" % str(e))
            self.main.prg_widget.gui.lblCancel.setText("")
            self.main.prg_widget.gui.close()
            return

        # try:
        # Set up the model and parse all parameters
        model_I.initialize_vectorized(LUT_dir=self.path, LUT_name=self.LUT_name, ns=self.ns,
                                      tts=self.dict_vals['tts'], tto=self.dict_vals['tto'], psi=self.dict_vals['psi'],
                                      N=self.dict_vals['N'], cab=self.dict_vals['cab'], cw=self.dict_vals['cw'],
                                      cm=self.dict_vals['cm'], LAI=self.dict_vals['LAI'], LIDF=self.dict_vals['LIDF'],
                                      typeLIDF=[2], hspot=self.dict_vals['hspot'], psoil=self.dict_vals['psoil'],
                                      car=self.dict_vals['car'], cbrown=self.dict_vals['cbrown'], soil=self.bg_spec,
                                      anth=self.dict_vals['anth'], cp=self.dict_vals['cp'],
                                      cbc=self.dict_vals['cbc'], LAIu=self.dict_vals['LAIu'],
                                      cd=self.dict_vals['cd'], sd=self.dict_vals['sd'], h=self.dict_vals['h'],
                                      prgbar_widget=self.main.prg_widget, qgis_app=self.main.qgis_app,
                                      depends=self.depends, depends_cp_cbc=self.depends_cp_cbc)

        # except ValueError as e:
        #     self.abort(message="An error occurred while creating the LUT: %s" % str(e))
        #     self.main.prg_widget.gui.lblCancel.setText("")
        #     self.main.prg_widget.gui.close()
        #     return

        QMessageBox.information(self.gui, "Successful", "The Look-Up-Table has successfully been created!")
        self.main.prg_widget.gui.lblCancel.setText("")
        self.main.prg_widget.gui.allow_cancel = True
        self.main.prg_widget.gui.close()

    def abort(self, message):
        QMessageBox.critical(self.gui, "Error", message)

    def open_file(self, type):
        self.main.loadtxtfile.open(type=type)

    def open_sensoreditor(self):
        self.main.sensoreditor.open()


# Class SensorEditor allows to create new .srf from text files that contain srf-information
class SensorEditor:
    mLayer: QgsMapLayerComboBox

    def __init__(self, main):
        self.main = main
        self.gui = SensorEditorGUI()
        self.connections()
        self.initial_values()

    def connections(self):
        self.gui.cmdOK.clicked.connect(lambda: self.ok())
        self.gui.cmdCancel.clicked.connect(self.gui.close)
        self.gui.cmdInputFile.clicked.connect(lambda: self.open_srf_file())
        self.gui.cmdWLFile.clicked.connect(lambda: self.open_wl_file())
        self.gui.radioHeader.toggled.connect(lambda: self.change_radioHeader())
        self.gui.cmbDelimiter.activated.connect(lambda: self.change_cmbDelimiter())
        self.gui.cmbWLunit.activated.connect(lambda: self.change_cmbWLunit())

        self.gui.cmdInputImage.clicked.connect(lambda: self.open_image(mode="imgSelect"))
        self.gui.mLayer.layerChanged.connect(lambda: self.open_image(mode="imgDropdown"))

    def initial_values(self):
        self.header_bool, self.delimiter, self.wl_convert = (None, None, None)
        self.filenamesIn, self.wl_filename = (None, None)
        self.image = None
        self.current_path = APP_DIR + "/Resources/Spec2Sensor/srf"  # change this, if the relative path
        # of the srfs changes
        self.flag_wl, self.flag_srf, self.flag_image = (False, False, False)
        self.delimiter_str = ["Tab", "Space", ",", ";"]  # delimiters can be added here
        self.wlunit_str = ["nm", "µm"]
        self.gui.cmbDelimiter.clear()
        self.gui.cmbDelimiter.addItems(self.delimiter_str)
        self.gui.cmbWLunit.clear()
        self.gui.cmbWLunit.addItems(self.wlunit_str)
        self.gui.tablePreview.setRowCount(0)
        self.gui.tablePreview.setColumnCount(0)
        self.gui.radioHeader.setDisabled(True)
        self.gui.radioHeader.setChecked(False)
        self.gui.cmbDelimiter.setDisabled(True)
        self.gui.cmbWLunit.setDisabled(True)
        self.gui.lineSensorname.setDisabled(True)
        self.gui.cmdOK.setDisabled(True)
        self.gui.label.setStyleSheet("color: rgb(170, 0, 0);")
        self.gui.label.setText("No File selected")
        self.gui.lblInputFile.setText("")
        self.addItem = []
        self.gui.mLayer.setLayer(None)

    def open_srf_file(self):
        self.gui.tablePreview.setRowCount(0)
        self.gui.tablePreview.setColumnCount(0)
        self.gui.tablePreview.clear()
        # Open files for the srf; look in self.current_path per default
        # Each file contains one column for wavelengths and one for weights
        # Each file represents one band of the target sensor
        file_choice, _filter = QFileDialog.getOpenFileNames(parent=None, caption='Select sensor file(s)',
                                                            directory=self.current_path, filter="(*.*)")
        if not file_choice:
            return
        self.filenamesIn = file_choice
        self.current_path = os.path.dirname(self.filenamesIn[0])  # set current_path and remember for next time
        filenames_display = ", ".join(j for j in [os.path.basename(i) for i in self.filenamesIn])  # string of all files
        self.gui.lblInputFile.setText(filenames_display)
        self.gui.radioHeader.setEnabled(True)
        self.gui.cmbDelimiter.setEnabled(True)
        self.gui.cmbWLunit.setEnabled(True)
        self.gui.lineSensorname.setEnabled(True)
        self.gui.mLayer.setEnabled(False)
        self.read_file()

    def read_file(self):
        # BuildTrueSRF is a Spec2Sensor class
        self.build_true_srf = BuildTrueSRF(srf_files=self.filenamesIn, header_bool=self.header_bool,
                                           delimiter=self.delimiter,
                                           wl_convert=self.wl_convert)
        return_flag, self.srf_list = self.build_true_srf.dframe_from_txt()
        if not return_flag:
            self.houston(message=self.srf_list, reset_table_preview=True)
            return

        nbands_sensor = len(self.srf_list)  # how many bands in the target sensor?
        srf_nbands = [len(self.srf_list[i][0]) for i in range(nbands_sensor)]  # how many srf values per band?

        self.delimiter = self.build_true_srf.delimiter
        self.gui.cmbDelimiter.blockSignals(True)  # block signals to avoid a trigger when cmbDelimiter is changes
        # the delimiter has been automatically detected, now set cmbDelimiter accordingly
        if self.delimiter == "\t":
            self.gui.cmbDelimiter.setCurrentIndex(0)
        elif self.delimiter == " ":
            self.gui.cmbDelimiter.setCurrentIndex(1)
        elif self.delimiter == ",":
            self.gui.cmbDelimiter.setCurrentIndex(2)
        elif self.delimiter == ";":
            self.gui.cmbDelimiter.setCurrentIndex(3)
        self.gui.cmbDelimiter.blockSignals(False)

        self.header_bool = self.build_true_srf.header_bool  # do the srf-files contain headers?
        self.gui.radioHeader.blockSignals(True)
        self.gui.radioHeader.setChecked(self.header_bool)  # check radioButton accordingly
        self.gui.radioHeader.blockSignals(False)

        self.wl_convert = self.build_true_srf.wl_convert
        if self.wl_convert == 1:
            self.gui.cmbWLunit.setCurrentIndex(1)  # presumably µm
        elif self.wl_convert == 1000:
            self.gui.cmbWLunit.setCurrentIndex(0)  # presumably nm

        # populate QTableWidget:
        wavelengths_str = ['(band {:00d}) wavelengths'.format(band + 1) for band in range(nbands_sensor)]
        header_items = [j for i in zip(wavelengths_str, ['weights'] * nbands_sensor) for j in i]  # build header as str
        nrows = np.max(srf_nbands)
        ncols = nbands_sensor * 2
        self.gui.tablePreview.setRowCount(nrows)  # how many rows do we need?
        self.gui.tablePreview.setColumnCount(ncols)  # how many cols do we need?
        self.gui.tablePreview.setHorizontalHeaderLabels(header_items)

        # build new array with discrete size:
        # dim 0: longest vector of srf_nbands, i.e. the band that takes into account the most weights, defines the shape
        # dim 1: number of bands for the target sensor
        # dim 2: [0] wavelengths; [1] weights
        new_srf = np.full(shape=(np.max(srf_nbands), nbands_sensor, 2), fill_value=np.nan, dtype=np.float64)
        for band in range(nbands_sensor):  # fill values into new_srf
            new_srf[0:srf_nbands[band], band, 0] = np.asarray(
                self.srf_list[band][0][:srf_nbands[band]]) / self.wl_convert
            new_srf[0:srf_nbands[band], band, 1] = np.asarray(self.srf_list[band][1][:srf_nbands[band]])

        for row in range(nrows):
            for col in range(0, ncols, 2):  # in the QTablePreview Widget, cols are doubled (wl, weight),
                # in the array, they are not
                wl = new_srf[row, col // 2, 0]

                # most bands have shorter lengths in srf_nbands, these are filled with np.nan -> sort them out
                if np.isnan(wl):
                    item_wl = QTableWidgetItem("")
                    item_weigh = QTableWidgetItem("")
                else:
                    item_wl = QTableWidgetItem(str(new_srf[row, col // 2, 0]))
                    item_weigh = QTableWidgetItem(str(new_srf[row, col // 2, 1]))
                self.gui.tablePreview.setItem(row, col, item_wl)  # place wavelength item
                self.gui.tablePreview.setItem(row, col + 1, item_weigh)  # place weight item

        self.gui.tablePreview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.flag_srf = True
        self.flag_image = False
        self.check_flags()  # check if the app is ready to be run

    def open_image(self, mode):  # open image
        self.gui.tablePreview.setRowCount(0)
        self.gui.tablePreview.setColumnCount(0)
        self.gui.tablePreview.clear()
        self.image = None
        if mode == "imgSelect":

            bsq_input = QFileDialog.getOpenFileName(caption='Select Input Image')[0]
            if not bsq_input:
                return
            self.addItem.append(bsq_input)
            self.gui.mLayer.setAdditionalItems(self.addItem)
            self.gui.mLayer.setCurrentText(bsq_input)

            if len(self.addItem) > 1:
                self.image = bsq_input
                self.image_read()

        elif mode == "imgDropdown":
            self.gui.tablePreview.clear()
            if self.gui.mLayer.currentLayer() is not None:
                input = self.gui.mLayer.currentLayer()
                bsq_input = input.source()
            elif len(self.gui.mLayer.currentText()) > 0:
                bsq_input = self.gui.mLayer.currentText()
            else:
                return
            self.image = bsq_input
            self.image_read()

        self.gui.lineSensorname.setEnabled(True)
        self.flag_image = True
        self.flag_srf = False
        self.gui.radioHeader.setDisabled(True)
        self.gui.radioHeader.setChecked(False)
        self.gui.cmbDelimiter.setDisabled(True)
        self.gui.cmbWLunit.setDisabled(True)
        self.gui.lblInputFile.setText("")
        self.gui.mLayer.setEnabled(True)
        self.check_flags()

    def image_read(self):  # read only necessary info: fwhm and center wavelengths
        inras = self.image
        image = openRasterDataset(inras)
        meta = image.metadataDict()
        try:
            fwhm = meta['ENVI']['fwhm']
            wavelength = meta['ENVI']['wavelength']
        except ImportError:
            self.houston(message="Missing wavelength and/or FWHM information"
                                 "Make sure input imagery is ENVI bsq with wavelength and fwhm provided")

        fwhm = [float(i) for i in fwhm]
        wavelength = [float(i) for i in wavelength]
        self.outreach = [i for i, v in enumerate(wavelength) if v < 400 or v > 2500]

        x = np.array(list(zip(wavelength, fwhm)))
        nbands_sensor = len(wavelength)

        header_items = ['Wavelength', 'FWHM']  # build header as str
        nrows = nbands_sensor
        ncols = 2
        self.gui.tablePreview.setRowCount(nrows)  # how many rows do we need?
        self.gui.tablePreview.setColumnCount(ncols)  # how many cols do we need?
        for row in range(nbands_sensor):
            wl_item = QTableWidgetItem("%.2f" % x[row, 0])
            fwhm_item = QTableWidgetItem("%2.f" % x[row, 1])
            self.gui.tablePreview.setItem(row, 0, wl_item)
            self.gui.tablePreview.setItem(row, 1, fwhm_item)
        for i in self.outreach:
            self.gui.tablePreview.item(i, 0).setBackground(QColor(200, 0, 0))
        self.gui.tablePreview.setHorizontalHeaderLabels(header_items)
        self.gui.tablePreview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        wavelength_srf = np.delete(wavelength, self.outreach)
        fwhm_srf = np.delete(fwhm, self.outreach)
        self.x = np.array(list(zip(wavelength_srf, fwhm_srf)))

        self.build_generic_srf = BuildGenericSRF(imagery=self.image)

    def open_wl_file(self):
        # SensorEdit needs a wavelength file with one column that contains the central wavelengths of the target sensor
        file_choice, _filter = QFileDialog.getOpenFileName(parent=None, caption='Select Wavelength File',
                                                           directory=self.current_path, filter="(*.*)")

        if not file_choice:
            return

        try:
            _ = np.loadtxt(file_choice)  # try to open the file
        except:
            self.houston(message="Error loading file with wavelengths. "
                                 "Make sure to provide a single-column file without header")
            self.wl_filename = None
            self.flag_wl = False
            return
        self.wl_filename = file_choice
        self.current_path = os.path.dirname(self.wl_filename)  # update the current path
        self.gui.lblWLFile.setText(self.wl_filename)
        self.flag_wl = True
        self.check_flags()  # check if all infos are provided and the tool can be run

    def open(self):
        self.initial_values()
        self.gui.setWindowTitle("Create New Sensor")
        self.gui.show()

    def change_radioHeader(self):
        self.header_bool = self.gui.radioHeader.isChecked()
        self.read_file()

    def change_cmbDelimiter(self):
        index = self.gui.cmbDelimiter.currentIndex()
        if index == 0:
            self.delimiter = "\t"
        elif index == 1:
            self.delimiter = " "
        elif index == 2:
            self.delimiter = ","
        elif index == 3:
            self.delimiter = ";"
        self.read_file()

    def change_cmbWLunit(self):
        index = self.gui.cmbWLunit.currentIndex()
        if index == 0:
            self.wl_conversion = 1
        elif index == 1:
            self.wl_conversion = 1000

    def houston(self, message, reset_table_preview=False, disable_cmdOK=True):
        # Houston, we have a problem
        self.gui.label.setStyleSheet("color: rgb(170, 0, 0);")
        self.gui.label.setText(message)
        if reset_table_preview:
            self.gui.tablePreview.setRowCount(0)
            self.gui.tablePreview.setColumnCount(0)
        if disable_cmdOK:
            self.gui.cmdOK.setDisabled(True)

    def check_flags(self):
        if self.flag_srf and self.flag_wl and not self.flag_image:
            self.gui.label.setStyleSheet("color: rgb(0, 170, 0);")
            self.gui.label.setText("Create True SRF Inputs OK. No Errors")
            self.gui.cmdOK.setEnabled(True)
        elif self.flag_srf and not self.flag_wl and not self.flag_image:
            self.gui.label.setStyleSheet("color: rgb(170, 130, 0);")
            self.gui.label.setText("SRF-File OK. Check Wavelength-File!")
        elif not self.flag_srf and self.flag_wl and not self.flag_image:
            self.gui.label.setStyleSheet("color: rgb(170, 130, 0);")
            self.gui.label.setText("Wavelength-File OK. Check SRF-File!")
        elif self.flag_image and not self.flag_wl and not self.flag_srf:
            self.gui.label.setStyleSheet("color: rgb(0, 170, 0);")
            text = "Create Generic SRF from Imagery OK: " + str(len(self.x[:, 0])) + " Bands."
            self.gui.label.setText(text)
            if len(self.outreach) > 0:
                text = "Create Generic SRF from Imagery OK with " + str(
                    len(self.x[:, 0])) + " Bands but Caution! " + str(len(self.outreach)) + \
                       " wavelengths outside PROSAIL range will be deleted!"
                self.gui.label.setStyleSheet("color: rgb(170, 130, 0);")
                self.gui.label.setText(text)
            self.gui.cmdOK.setEnabled(True)
            self.gui.mLayer.setEnabled(True)

    def ok(self):
        # do the actual work of the SensorEdit class
        sensor_name = self.gui.lineSensorname.text()
        if not sensor_name:
            self.houston(message="Sensor name missing!", disable_cmdOK=False)
            return
        elif not self.main.LUT.gui.SType_combobox.findText(sensor_name) == -1:
            self.houston(message="A sensor with this name already exists in the list!", disable_cmdOK=False)
            return
        if self.flag_srf and self.flag_wl and not self.flag_image:
            # A numpy array file is created from the sensor srf files and the wavelength file
            # it is first saved as .npz format and renamed to .srf afterward
            self.build_true_srf.wl_file = self.wl_filename
            self.build_true_srf.out_file = APP_DIR + "/Resources/Spec2Sensor/srf/" + sensor_name + ".npz"
            # call the build_true_srf routine from Spec2Sensor
            return_flag, sensor_name = self.build_true_srf.srf_from_dframe(srf_list=self.srf_list)
            if not return_flag:
                self.houston(message=sensor_name)
                return
            else:
                QMessageBox.information(self.gui, "Done",
                                        "SRF-file created. It can be now used within IVVRM and CreateLUT")
            self.main.LUT.init_sensorlist()
            # set index of the combobox to new sensor
            sensor_index = self.main.LUT.gui.SType_combobox.findText(sensor_name)
            if sensor_index >= 0:  # sensor_index is -1 if the sensor creation failed; in this case, don't update sensor
                self.main.LUT.gui.SType_combobox.setCurrentIndex(sensor_index)
            self.gui.close()
        if self.flag_image and not self.flag_wl and not self.flag_srf:
            self.build_generic_srf.out_file = APP_DIR + "/Resources/Spec2Sensor/srf/" + sensor_name + ".npz"
            return_flag, full_path, sensor_name = self.build_generic_srf.srf_from_imagery(x=self.x)
            if not return_flag:
                self.houston(message=sensor_name)
                return
            else:
                QMessageBox.information(self.gui, "Done",
                                        "SRF-file created. It can be now used within IVVRM and CreateLUT")
                self.main.LUT.init_sensorlist()


# LoadTxtFile is a class to open a new GUI in which a text file is opened which needs to meet certain criteria
# In this case, it's the background spectrum which needs to be a two column text file with wavelengths and
# reflectance values.
class LoadTxtFile:
    def __init__(self, main):
        self.main = main
        self.gui = LoadTxtFileGUI()
        self.connections()
        self.initial_values()

    def connections(self):
        self.gui.cmdOK.clicked.connect(lambda: self.ok())
        self.gui.cmdCancel.clicked.connect(self.gui.close)
        self.gui.cmdInputFile.clicked.connect(lambda: self.open_file())
        self.gui.radioHeader.toggled.connect(lambda: self.change_radioHeader())
        self.gui.cmbDelimiter.activated.connect(lambda: self.change_cmbDelimiter())  # "activated" signal is only called
        # for user activity, not code call
        self.gui.spinDivisionFactor.valueChanged.connect(lambda: self.change_division())

    def initial_values(self):
        self.header_bool = None
        self.filenameIn = None
        self.delimiter_str = ["Tab", "Space", ",", ";"]
        self.gui.cmbDelimiter.clear()
        self.gui.cmbDelimiter.addItems(self.delimiter_str)
        self.gui.tablePreview.setRowCount(0)
        self.gui.tablePreview.setColumnCount(0)
        self.gui.radioHeader.setDisabled(True)
        self.gui.radioHeader.setChecked(False)
        self.gui.cmbDelimiter.setDisabled(True)
        self.gui.spinDivisionFactor.setDisabled(True)
        self.gui.spinDivisionFactor.setValue(1.0)
        self.gui.cmdOK.setDisabled(True)
        self.gui.label.setStyleSheet("color: rgb(170, 0, 0);")
        self.gui.label.setText("No File selected")
        self.gui.lblInputFile.setText("")
        self.divide_by = 1.0
        self.open_type = None
        self.wl_open, self.data_mean, self.nbands = (None, None, None)

    def open(self, type):
        self.initial_values()
        # the type of "open" can be set. It is always "background" in this .py, but the routine can be copied and
        # used for other purposes as well!
        self.open_type = type
        self.gui.setWindowTitle("Open %s Spectrum" % type)
        self.gui.show()

    def open_file(self):
        file_choice, _filter = QFileDialog.getOpenFileName(None, 'Select Spectrum File', '.', "(*.txt *.csv)")
        if not file_choice:  # Cancel clicked
            if not self.filenameIn:
                self.houston(message="No File selected")  # plus: no file in memory
            return
        self.filenameIn = file_choice
        self.gui.lblInputFile.setText(self.filenameIn)
        self.gui.radioHeader.setEnabled(True)
        self.gui.cmbDelimiter.setEnabled(True)
        self.gui.spinDivisionFactor.setEnabled(True)
        self.header_bool = False
        self.inspect_file()

    def inspect_file(self):
        # Look into the file and detect the delimiter and if it has a header
        sniffer = csv.Sniffer()  # the csv.Sniffer detects the "dialect" of the text file
        with open(self.filenameIn, 'r') as raw_file:
            self.dialect = sniffer.sniff(raw_file.readline())
            if self.dialect.delimiter == "\t":
                self.gui.cmbDelimiter.setCurrentIndex(0)
            elif self.dialect.delimiter == " ":
                self.gui.cmbDelimiter.setCurrentIndex(1)
            elif self.dialect.delimiter == ",":
                self.gui.cmbDelimiter.setCurrentIndex(2)
            elif self.dialect.delimiter == ";":
                self.gui.cmbDelimiter.setCurrentIndex(3)
            raw_file.seek(0)  # rewind the file to the beginning
            raw = csv.reader(raw_file, self.dialect)
            try:
                # if the first row can be converted to int, it most likely does not contain a header
                _ = int(next(raw)[0])
                self.header_bool = False
            except ValueError:
                self.header_bool = True
            self.gui.radioHeader.setChecked(self.header_bool)
            self.read_file()  # now read the file for good with the information you have

    def change_radioHeader(self):
        self.header_bool = self.gui.radioHeader.isChecked()
        self.read_file()

    def change_cmbDelimiter(self):
        index = self.gui.cmbDelimiter.currentIndex()
        if index == 0:
            self.dialect.delimiter = "\t"
        elif index == 1:
            self.dialect.delimiter = " "
        elif index == 2:
            self.dialect.delimiter = ","
        elif index == 3:
            self.dialect.delimiter = ";"
        self.read_file()

    def change_division(self):
        self.divide_by = self.gui.spinDivisionFactor.value()
        self.read_file()

    def read_file(self):
        if not self.filenameIn:
            return

        header_offset = 0

        with open(self.filenameIn, 'r') as raw_file:
            raw_file.seek(0)
            raw = csv.reader(raw_file, self.dialect)
            data = list()
            for content in raw:
                data.append(content)  # write the content of the file to "data"

        n_entries = len(data)
        if self.header_bool:
            header = data[0]  # if file has a header, first row is taken as header
            if not len(header) == len(data[1]):  # header needs to have as many columns as the rest of the data
                self.houston(
                    message="Error: Data has %i columns, but header has %i columns" % (len(data[1]), len(header)))
                return
            header_offset += 1
            n_entries -= 1
        n_cols = len(data[0 + header_offset])
        try:
            self.wl_open = [float(data[i + header_offset][0]) for i in range(n_entries)]  # read wavelengths
        except ValueError:
            self.houston(message="Error: Cannot read file. Please check delimiter and header!")
            return

        # row labels of the QTableWidget are the actual data
        row_labels = [str(self.wl_open[i]) for i in range(n_entries)]

        wl_offset = 400 - self.wl_open[0]  # PROSAIL wavelengths start at 400, consider an offset if necessary

        data_array = np.zeros(shape=(n_entries, n_cols - 1))  # prepare for reading the data into numpy array
        for data_list in range(n_entries):
            data_array[data_list, :] = np.asarray(data[data_list + header_offset][1:]).astype(dtype=np.float16)

        # The user may choose to have several columns in his/her text file; in this case, the mean of all backgrounds
        # is calculated, although in most cases it is expected to be a single column of reflectance data
        self.data_mean = np.mean(data_array, axis=1) / self.divide_by

        # populate QTableWidget:
        self.gui.tablePreview.setRowCount(n_entries)
        self.gui.tablePreview.setColumnCount(1)
        if self.header_bool:
            # "bla" is just dummy and will not be displayed
            self.gui.tablePreview.setHorizontalHeaderLabels(('Reflectances', 'bla'))
        self.gui.tablePreview.setVerticalHeaderLabels(row_labels)

        # Place the data of the text file into the QTableWidget
        for row in range(n_entries):
            item = QTableWidgetItem(str(self.data_mean[row]))  # convert text string to a QTableWidgetItem Object
            self.gui.tablePreview.setItem(row, 0, item)  # setItem(row, col, content)

        # Prepare for Statistics
        if wl_offset > 0:
            self.data_mean = self.data_mean[wl_offset:]  # cut off first 50 Bands to start at Band 400
            self.wl_open = self.wl_open[wl_offset:]

        self.gui.label.setStyleSheet("color: rgb(0, 170, 0);")
        self.gui.label.setText("Ok. No Errors")
        self.gui.cmdOK.setEnabled(True)

    def houston(self, message):
        # Houston, we have a problem
        self.gui.label.setStyleSheet("color: rgb(170, 0, 0);")
        self.gui.label.setText(message)
        self.gui.tablePreview.setRowCount(0)
        self.gui.tablePreview.setColumnCount(0)
        self.gui.cmdOK.setDisabled(True)

    def ok(self):
        self.nbands = len(self.wl_open)
        self.main.LUT.wl_open = self.wl_open  # communicate with th LUT class to pass the wavelengths
        self.main.select_wavelengths.populate()  # communicate with select_wavelenghts class to pass wavelengths
        self.main.select_wavelengths.gui.setModal(True)  # the new windows is modal, it cannot be ignored
        self.main.select_wavelengths.gui.show()
        self.gui.close()


# The SelectWavelengths class allows to add/remove wavelengths from a model
# In this case it is used to use wavelengths of a certain background as basis for the LUT
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

    def populate(self):
        if self.main.loadtxtfile.nbands < 10:
            width = 1
        elif self.main.loadtxtfile.nbands < 100:
            width = 2
        elif self.main.loadtxtfile.nbands < 1000:
            width = 3
        else:
            width = 4

        # These are the wavelengths of atmospheric water vapor absorption; any bands with central wavelengths
        # in this domain are excluded by default, i.e. the GUI is prepared to add these to the exclude list
        self.default_exclude = [i for j in
                                (range(0, 400), range(960, 1021), range(1390, 1551), range(2000, 2101),
                                 range(2500, 10000)) for i in j]

        for i in range(self.main.loadtxtfile.nbands):
            if i in self.default_exclude:
                str_band_no = '{num:0{width}}'.format(num=i + 1, width=width)
                label = "band %s: %6.2f %s" % (str_band_no, self.main.loadtxtfile.wl_open[i], u'nm')
                self.gui.lstExcluded.addItem(label)
            else:
                str_band_no = '{num:0{width}}'.format(num=i + 1, width=width)
                label = "band %s: %6.2f %s" % (str_band_no, self.main.loadtxtfile.wl_open[i], u'nm')
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
            list_object = self.gui.lstIncluded
            direction = "in_to_ex"
        elif select == "none":
            list_object = self.gui.lstExcluded
            direction = "ex_to_in"

        for i in range(list_object.count()):
            item = list_object.item(i)
            list_object.setItemSelected(item, True)

        self.send(direction=direction)

    def ok(self):
        list_object = self.gui.lstExcluded
        raw_list = []
        for i in range(list_object.count()):  # read from the QtObect "list" all items as text
            item = list_object.item(i).text()
            raw_list.append(item)

        # convert the text-string of the list object into a python list of integers (bands to be excluded)
        exclude_bands = [int(raw_list[i].split(" ")[1][:-1]) - 1 for i in range(len(raw_list))]

        # convert the single bands to ranges in which the background signal will be interpolated
        water_absorption_ranges = self.generate_ranges(range_list=exclude_bands)

        # the following loop iterates over all ranges of excluded bands (e.g absorption ranges of atm. water vap.)
        # and performs a simple linear interpolation in between to overwrite the actual signal
        # y is the data from the textfile in the exclude ranges
        # f is the interpolated representation
        for interp_bands in water_absorption_ranges:
            y = [self.main.loadtxtfile.data_mean[interp_bands[0]], self.main.loadtxtfile.data_mean[interp_bands[-1]]]
            f = interp1d([interp_bands[0], interp_bands[-1]], [y[0], y[1]])
            self.main.loadtxtfile.data_mean[interp_bands[1:-1]] = f(interp_bands[1:-1])

        # set the bg_spec to the reflectances of the text file with the interpolated ranges
        self.main.LUT.bg_spec = self.main.loadtxtfile.data_mean
        self.main.LUT.gui.BackSpec_label.setText(os.path.basename(self.main.loadtxtfile.filenameIn))
        self.main.LUT.gui.push_SelectFile.setEnabled(False)
        self.main.LUT.gui.push_SelectFile.setText('File:')

        # clean up
        for list_object in [self.gui.lstIncluded, self.gui.lstExcluded]:
            list_object.clear()

        self.gui.close()

    def generate_ranges(self, range_list):
        # this function groups single exclude bands to ranges
        water_absorption_ranges = list()
        last = -2
        start = -1

        for item in range_list:
            if item != last + 1:
                if start != -1:
                    water_absorption_ranges.append(range(start, last + 1))
                start = item
            last = item
        water_absorption_ranges.append(range(start, last + 1))
        return water_absorption_ranges


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
        self.qgis_app = QApplication.instance()  # the qgis-Application is made accessible within the code
        self.LUT = LUT(self)
        self.sensoreditor = SensorEditor(self)
        self.loadtxtfile = LoadTxtFile(self)
        self.select_wavelengths = SelectWavelengths(self)
        self.prg_widget = PRG(self)

    def show(self):
        self.LUT.gui.show()


if __name__ == '__main__':
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from enmapbox.testing import start_app

    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())
