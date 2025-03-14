# -*- coding: utf-8 -*-
"""
***************************************************************************
    IVVRM_GUI.py - LMU Agri Apps - Interactive Visualization of Vegetation Reflectance Models (IVVRM)
    -----------------------------------------------------------------------
    begin                : 01/2018
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

import sys
import os
import numpy as np
from scipy.interpolate import interp1d
# from qgis.gui import *

# ensure to call QGIS before PyQtGraph
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from enmapbox.qgispluginsupport.qps.pyqtgraph import pyqtgraph as pg
from lmuvegetationapps.Resources.PROSAIL import call_model as mod
from lmuvegetationapps.Resources.Spec2Sensor.Spec2Sensor_core import Spec2Sensor, BuildTrueSRF, BuildGenericSRF
from lmuvegetationapps import APP_DIR

from qgis.gui import QgsMapLayerComboBox
from _classic.hubflow.core import *

import warnings

warnings.filterwarnings('ignore')  # ignore warnings, like ZeroDivision

import csv
from enmapbox.gui.utils import loadUi

pathUI_IVVRM = os.path.join(APP_DIR, 'Resources/UserInterfaces/IVVRM_main.ui')
pathUI_loadtxt = os.path.join(APP_DIR, 'Resources/UserInterfaces/LoadTxtFile.ui')
pathUI_wavelengths = os.path.join(APP_DIR, 'Resources/UserInterfaces/Select_Wavelengths.ui')
pathUI_sensor = os.path.join(APP_DIR, 'Resources/UserInterfaces/GUI_SensorEditor.ui')


class IVVRM_GUI(QDialog):
    def __init__(self, parent=None):
        super(IVVRM_GUI, self).__init__(parent)
        loadUi(pathUI_IVVRM, self)

        # fix the sendHoverEvent crash by replacing the slot function
        self.graphicsView.scene().sendHoverEvents = self.onHoverEvent
        self.graphicsView.setBackground(QColor('black'))

        self.plotItem = self.graphicsView.getPlotItem()
        # assert isinstance(self.plotItem, pg.PlotItem)
        self.viewBox = self.plotItem.getViewBox()
        # assert isinstance(self.viewBox, pg.ViewBox)
        self.viewBoxMenu = self.viewBox.menu
        # assert isinstance(self.viewBoxMenu, QMenu)
        # assert isinstance(self.viewBoxMenu, pg.ViewBoxMenu.ViewBoxMenu)

        # add color settings to the viewbox context menu
        from qgis.gui import QgsColorButton
        self.btnBackgroundColor = QgsColorButton()

        self.btnBackgroundColor.colorChanged.connect(self.setBackgroundColor)
        self.btnAxisColor = QgsColorButton()
        self.btnAxisColor.colorChanged.connect(self.setAxisColor)

        l = QGridLayout()
        l.addWidget(QLabel('Background'), 0, 0)
        l.addWidget(self.btnBackgroundColor, 0, 1)
        l.addWidget(QLabel('Axes'), 1, 0)
        l.addWidget(self.btnAxisColor, 1, 1)

        self.colorWidget = QWidget()
        self.colorWidget.setLayout(l)
        self.viewBoxMenu.addSeparator()
        m = self.viewBoxMenu.addMenu('Plot Colors')
        wa = QWidgetAction(m)
        wa.setDefaultWidget(self.colorWidget)
        m.addAction(wa)

        # set default colors
        self.setBackgroundColor('black')
        self.setAxisColor('white')

    def setAxisColor(self, color: QColor):
        if not isinstance(color, QColor):
            color = QColor(color)
        assert isinstance(color, QColor)
        if color != self.btnAxisColor.color():
            # changing btnAxisColor.color() will trigger setAxisColor again
            self.btnAxisColor.setColor(color)
        else:
            for name in self.plotItem.axes.keys():
                ax = self.plotItem.getAxis(name)
                if ax:
                    ax.setPen(QColor(color))
                    ax.setTextPen(QColor(color))

    def setBackgroundColor(self, color: QColor):
        if not isinstance(color, QColor):
            color = QColor(color)
        assert isinstance(color, QColor)
        if color != self.btnBackgroundColor.color():
            self.btnBackgroundColor.setColor(color)
        else:
            # self.btnBackgroundColor.setColor(QColor(color))
            self.graphicsView.setBackground(QColor(color))

    def onHoverEvent(self, *args, **kwds):
        """
        Does nothing. Just to avoid calling the PyQtGraph routine which can fail
        """
        pass


class LoadTxtFileGUI(QDialog):
    def __init__(self, parent=None):
        super(LoadTxtFileGUI, self).__init__(parent)
        loadUi(pathUI_loadtxt, self)


class SelectWavelengthsGUI(QDialog):
    def __init__(self, parent=None):
        super(SelectWavelengthsGUI, self).__init__(parent)
        loadUi(pathUI_wavelengths, self)


class SensorEditorGUI(QDialog):
    def __init__(self, parent=None):
        super(SensorEditorGUI, self).__init__(parent)
        loadUi(pathUI_sensor, self)


# class StartIVVRM pops up the welcome window with the PROSAIL image and a Start-button
# class StartIVVRM:
#     def __init__(self, main):
#         self.main = main
#         self.gui = IVVRM_Start_GUI()
#         self.initial_values()
#         self.connections()
#
#     def initial_values(self):
#         self.gui.setWindowTitle('IVVRM')
#
#     def connections(self):
#         self.gui.startButton.clicked.connect(lambda: self.run_IVVRM())
#
#     def run_IVVRM(self):
#         self.main.ivvrm.gui.show()
#         self.main.ivvrm.plotting()
#         self.gui.close()


# class IVVRM is the main class of the IVVRM GUI to control the application
class IVVRM:

    def __init__(self, main):
        self.mPlotItems = []  # a list that stores the current plot items, i.e. single profiles.
        self.main = main
        self.gui = IVVRM_GUI()
        self.special_chars()  # place special characters that could not be set in Qt Designer
        self.initial_values()
        self.update_slider_pos()
        self.update_lineEdit_pos()
        self.deactivate_sliders()
        self.init_sensorlist()
        self.para_init()
        self.select_model()
        self.mod_interactive()
        self.mod_exec()

    def special_chars(self):
        # Set the following special characters (could not be set in Qt Designer)
        self.gui.lblCab.setText(u'[µg/cm²]')
        self.gui.lblCm.setText(u'[g/cm²]')
        self.gui.lblCar.setText(u'[µg/cm²]')
        self.gui.lblCanth.setText(u'[µg/cm²]')
        self.gui.lblCp.setText(u'[g/cm²]')
        # self.gui.lblLAI.setText(u'[m²/m²]')
        self.gui.lblCbc.setText(u'[g/cm²]')

    def initial_values(self):
        self.lop = "prospectD"
        self.canopy_arch = "sail"

        # the colors (tuple of R, G, B) for accumulative plotting; each PROSAIL variable gets its own color to recognize
        # add new colors if new variables are added; the order is the same as in self.lineEdits and self.para_names
        self.colors = [tuple([219, 183, 255]), tuple([51, 204, 51]), tuple([69, 30, 234]), tuple([0, 255, 255]),
                       tuple([255, 255, 0]), tuple([0, 0, 0]), tuple([255, 0, 0]), tuple([255, 255, 255]),
                       tuple([255, 124, 128]), tuple([178, 178, 178]), tuple([144, 204, 154]),
                       tuple([255, 153, 255]), tuple([25, 41, 70]), tuple([169, 139, 100]), tuple([50, 255, 50]),
                       tuple([255, 153, 51]), tuple([204, 0, 153]), tuple([172, 86, 38]), tuple([0, 100, 0]),
                       tuple([255, 128, 0]), tuple([153, 76, 0]), tuple([153, 0, 0])]
        self.lineEdits = [self.gui.N_lineEdit, self.gui.Cab_lineEdit, self.gui.Cw_lineEdit, self.gui.Cm_lineEdit,
                          self.gui.LAI_lineEdit, self.gui.lblFake, self.gui.LIDFB_lineEdit, self.gui.hspot_lineEdit,
                          self.gui.psoil_lineEdit, self.gui.SZA_lineEdit, self.gui.OZA_lineEdit, self.gui.rAA_lineEdit,
                          self.gui.Cp_lineEdit, self.gui.Cbc_lineEdit, self.gui.Car_lineEdit, self.gui.Canth_lineEdit,
                          self.gui.Cbrown_lineEdit, self.gui.LAIu_lineEdit, self.gui.CD_lineEdit, self.gui.SD_lineEdit,
                          self.gui.TreeH_lineEdit]
        self.para_names = ["N", "cab", "cw", "cm", "LAI", "typeLIDF", "LIDF", "hspot", "psoil", "tts", "tto", "psi",
                           "cp", "cbc", "car", "anth", "cbrown", "LAIu", "cd", "sd", "h"]
        # lineEdits_dict is a dictionary to link parameters to the lineEdit objects (text fields)
        self.lineEdits_dict = dict(zip(self.para_names, self.lineEdits))
        self.colors_dict = dict(zip(self.para_names, self.colors))  # do the same for the colors
        self.penStyle = 1
        self.item = 1
        self.plot_count = 0
        self.current_slider = None

        self.data_mean = None
        # dictionary for parameters is initialized with Nones
        self.para_dict = dict(zip(self.para_names, [None] * len(self.para_names)))
        self.para_dict["typeLIDF"] = 2  # 1: Distribution Functions, 2: Ellipsoidal (ALIA)
        self.bg_spec = None
        self.bg_type = "default"

    def init_sensorlist(self):
        list_dir = os.listdir(APP_DIR + "/Resources/Spec2Sensor/srf")

        # Get all files in the SRF directory
        list_allfiles = [item for item in list_dir if os.path.isfile(APP_DIR + "/Resources/Spec2Sensor/srf/" + item)]

        # Get all files from that list with extension .srf, but pop the extension to get the name of the sensor
        list_files = [item.split('.')[0] for item in list_allfiles if item.split('.')[1] == 'srf']

        list_files.insert(0, '400-2500 nm @ 1nm')  # Default entry is not read from .srf but written directly
        list_files.append("> Add new sensor...")  # How many sensors are available to choose from
        n_sensors = len(list_files)

        # block all Signals to avoid a trigger when adding/removing sensors from the list
        self.gui.SType_combobox.blockSignals(True)
        self.gui.SType_combobox.clear()
        self.gui.SType_combobox.addItems(list_files)
        self.gui.SType_combobox.blockSignals(False)  # turn the signals back on

        # Create a dictionary to map indices of the Dropdown to the files in the folder
        self.sensor_dict = dict(zip(range(n_sensors), list_files))
        self.sensor_dict[0] = 'default'  # rename 0th item, so that s2s knows to not post-process spectra
        self.sensor_dict[n_sensors - 1] = 'addnew'  # rename last item, so that GUI knows to open the sensor-editor

    def update_slider_pos(self):
        # call this, whenever any of the sliders in the GUI has been moved to find out which it was and
        # run PROSAIL afterwards
        self.gui.N_Slide.valueChanged.connect(lambda: self.any_slider_change(self.gui.N_Slide, self.gui.N_lineEdit))
        self.gui.Cab_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.Cab_Slide, self.gui.Cab_lineEdit))
        self.gui.Cw_Slide.valueChanged.connect(lambda: self.any_slider_change(self.gui.Cw_Slide, self.gui.Cw_lineEdit))
        self.gui.Cm_Slide.valueChanged.connect(lambda: self.any_slider_change(self.gui.Cm_Slide, self.gui.Cm_lineEdit))
        self.gui.Cp_Slide.valueChanged.connect(lambda: self.any_slider_change(self.gui.Cp_Slide, self.gui.Cp_lineEdit))
        self.gui.Cbc_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.Cbc_Slide, self.gui.Cbc_lineEdit))
        self.gui.Car_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.Car_Slide, self.gui.Car_lineEdit))
        self.gui.Canth_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.Canth_Slide, self.gui.Canth_lineEdit))
        self.gui.Cbrown_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.Cbrown_Slide, self.gui.Cbrown_lineEdit))
        self.gui.LAI_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.LAI_Slide, self.gui.LAI_lineEdit))
        self.gui.LIDFB_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.LIDFB_Slide, self.gui.LIDFB_lineEdit))
        self.gui.hspot_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.hspot_Slide, self.gui.hspot_lineEdit))
        self.gui.psoil_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.psoil_Slide, self.gui.psoil_lineEdit))
        self.gui.OZA_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.OZA_Slide, self.gui.OZA_lineEdit))
        self.gui.SZA_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.SZA_Slide, self.gui.SZA_lineEdit))
        self.gui.rAA_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.rAA_Slide, self.gui.rAA_lineEdit))
        self.gui.LAIu_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.LAIu_Slide, self.gui.LAIu_lineEdit))
        self.gui.SD_Slide.valueChanged.connect(lambda: self.any_slider_change(self.gui.SD_Slide, self.gui.SD_lineEdit))
        self.gui.TreeH_Slide.valueChanged.connect(
            lambda: self.any_slider_change(self.gui.TreeH_Slide, self.gui.TreeH_lineEdit))
        self.gui.CD_Slide.valueChanged.connect(lambda: self.any_slider_change(self.gui.CD_Slide, self.gui.CD_lineEdit))

    def update_lineEdit_pos(self):
        # call this function whenever a lineEdit has been changed, i.e. the user entered a value for one of the
        # PROSAIL variables manually
        self.gui.N_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.N_lineEdit, self.gui.N_Slide))
        self.gui.Cab_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Cab_lineEdit, self.gui.Cab_Slide))
        self.gui.Cw_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Cw_lineEdit, self.gui.Cw_Slide))
        self.gui.Cm_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Cm_lineEdit, self.gui.Cm_Slide))
        self.gui.Cp_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Cp_lineEdit, self.gui.Cp_Slide))
        self.gui.Cbc_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Cbc_lineEdit, self.gui.Cbc_Slide))
        self.gui.Car_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Car_lineEdit, self.gui.Car_Slide))
        self.gui.Canth_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Canth_lineEdit, self.gui.Canth_Slide))
        self.gui.Cbrown_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.Cbrown_lineEdit, self.gui.Cbrown_Slide))
        self.gui.LAI_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.LAI_lineEdit, self.gui.LAI_Slide))
        self.gui.LIDFB_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.LIDFB_lineEdit, self.gui.LIDFB_Slide))
        self.gui.hspot_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.hspot_lineEdit, self.gui.hspot_Slide))
        self.gui.psoil_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.psoil_lineEdit, self.gui.psoil_Slide))
        self.gui.OZA_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.OZA_lineEdit, self.gui.OZA_Slide))
        self.gui.SZA_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.SZA_lineEdit, self.gui.SZA_Slide))
        self.gui.rAA_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.rAA_lineEdit, self.gui.rAA_Slide))
        self.gui.LAIu_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.LAIu_lineEdit, self.gui.LAIu_Slide))
        self.gui.SD_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.SD_lineEdit, self.gui.SD_Slide))
        self.gui.TreeH_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.TreeH_lineEdit, self.gui.TreeH_Slide))
        self.gui.CD_lineEdit.returnPressed.connect(
            lambda: self.any_lineEdit_change(self.gui.CD_lineEdit, self.gui.CD_Slide))

    def any_slider_change(self, slider, which_lineEdit):
        # the function to find out which slider was changed
        if not self.current_slider == slider:  #
            self.plot_count += 1
        self.current_slider = slider
        my_value = str(slider.value() / 10000.0)
        which_lineEdit.setText(my_value)

    def any_lineEdit_change(self, which_lineEdit, slider):
        # the function to find out which lineEdit has received a new text
        try:
            my_value = int(float(which_lineEdit.text()) * 10000)  # check for validity of the user input
            slider.setValue(my_value)
        except ValueError:
            QMessageBox.critical(self.gui, "Not a number", "'%s' is not a valid number" % which_lineEdit.text())
            which_lineEdit.setText(str(slider.value() / 10000.0))

    def select_s2s(self, sensor_index, trigger=True):
        # function is called when a new sensor is chosen from the dropdown; if this is connected with a trigger,
        # execute Prosail afterwards to update the result in the new sensor type
        self.sensor = self.sensor_dict[sensor_index]
        if self.sensor == 'default':
            self.wl = range(400, 2501)
            self.gui.lblNoBands.setText("2101")
        elif self.sensor == 'addnew':  # user chose "add new sensor"
            self.open_sensoreditor()
            return
        else:
            s2s = Spec2Sensor(sensor=self.sensor, nodat=-999)
            sensor_init_success = s2s.init_sensor()
            if not sensor_init_success:
                return
            self.wl = s2s.wl_sensor
            self.plot_count += 1
            self.gui.lblNoBands.setText(str(s2s.n_wl_sensor))

        if trigger:
            self.makePen(sensor=self.sensor)
            self.mod_exec()

    def select_background(self, bg_type):
        # function is called when the background type is changed
        self.bg_type = bg_type

        if bg_type == "default":
            self.gui.B_DefSoilSpec.setEnabled(True)
            self.gui.B_LoadBackSpec.setEnabled(True)
            self.gui.BrightFac_Text.setEnabled(True)
            self.gui.psoil_Slide.setEnabled(True)
            self.gui.psoil_lineEdit.setEnabled(True)
            self.gui.push_SelectFile.setEnabled(False)
            self.gui.BackSpec_label.setEnabled(False)
            self.gui.BackSpec_label.setText("")
            self.bg_spec = None  # when bg_spec is None, PROSAIL will use the default soil
            self.mod_exec()

        elif bg_type == "load":
            self.gui.B_DefSoilSpec.setEnabled(True)
            self.gui.B_LoadBackSpec.setEnabled(True)
            self.gui.BrightFac_Text.setEnabled(False)
            self.gui.psoil_Slide.setEnabled(False)
            self.gui.psoil_lineEdit.setEnabled(False)
            self.gui.push_SelectFile.setEnabled(True)
            self.gui.push_SelectFile.setText('Select File...')
            self.gui.BackSpec_label.setEnabled(True)

    def makePen(self, sensor):
        # Different pen styles (solid, dashed, dotted, ...) are used for sensor types
        # print("Sensor is: ", sensor)
        if sensor == "default":
            self.penStyle = 1
        elif sensor == "EnMAP":
            self.penStyle = 3
        elif "Sentinel2" in sensor:  # could be "Sentinel2_full" or "Sentinel2_reduced"
            self.penStyle = 2
        elif sensor == "Landsat8":
            self.penStyle = 4
        else:
            self.penStyle = 5

    def select_LIDF(self, index):
        if index > 0:
            self.para_dict["typeLIDF"] = 1  # Beta Distribution
            self.para_dict["LIDF"] = index - 1
            self.gui.LIDFB_Slide.setDisabled(True)
            self.gui.LIDFB_lineEdit.setDisabled(True)
            self.mod_exec(item="LIDF")
        else:
            self.para_dict["typeLIDF"] = 2  # Ellipsoidal Distribution
            self.mod_exec(self.gui.LIDFB_Slide, item="LIDF")
            self.gui.LIDFB_Slide.setDisabled(False)
            self.gui.LIDFB_lineEdit.setDisabled(False)

    def deactivate_sliders(self):
        # Depending on the model type, some sliders need to be made unavailable to the user
        self.gui.B_Prospect4.clicked.connect(lambda: self.select_model(lop="prospect4", canopy_arch=self.canopy_arch))
        self.gui.B_Prospect5.clicked.connect(lambda: self.select_model(lop="prospect5", canopy_arch=self.canopy_arch))
        self.gui.B_Prospect5b.clicked.connect(lambda: self.select_model(lop="prospect5B", canopy_arch=self.canopy_arch))
        self.gui.B_ProspectD.clicked.connect(lambda: self.select_model(lop="prospectD", canopy_arch=self.canopy_arch))
        self.gui.B_ProspectPro.clicked.connect(
            lambda: self.select_model(lop="prospectPro", canopy_arch=self.canopy_arch))

        self.gui.B_LeafModelOnly.clicked.connect(lambda: self.select_model(lop=self.lop, canopy_arch="None"))
        self.gui.B_Sail_2M.clicked.connect(lambda: self.select_model(lop=self.lop, canopy_arch="sail2m"))
        self.gui.B_4Sail.clicked.connect(lambda: self.select_model(lop=self.lop, canopy_arch="sail"))
        self.gui.B_Inform.clicked.connect(lambda: self.select_model(lop=self.lop, canopy_arch="inform"))

    def select_model(self, lop="prospectD", canopy_arch="sail"):
        # arrange the GUI in accordance to the RTM selected
        self.lop = lop

        if canopy_arch == "None":
            self.canopy_arch = None
            self.gui.CanopyMP_Box.setDisabled(True)
            self.gui.ForestMP_Box.setDisabled(True)
            self.gui.BrightFac_Text.setEnabled(False)
            self.gui.psoil_Slide.setEnabled(False)
            self.gui.psoil_lineEdit.setEnabled(False)
            self.gui.push_SelectFile.setEnabled(False)
            self.gui.BackSpec_label.setEnabled(False)
            self.gui.B_DefSoilSpec.setEnabled(False)
            self.gui.B_LoadBackSpec.setEnabled(False)
            self.gui.LAI_Text.setText("Leaf Area Index (LAI)")

        elif canopy_arch == "inform":
            self.canopy_arch = canopy_arch
            self.gui.LAI_Text.setText("Single Tree Leaf Area Index (LAI)")
            self.gui.LAI_lineEdit.setText("7")
            self.gui.CanopyMP_Box.setDisabled(False)
            self.gui.ForestMP_Box.setDisabled(False)
            self.select_background(bg_type=self.bg_type)

        else:
            self.canopy_arch = canopy_arch
            self.gui.LAI_Text.setText("Leaf Area Index (LAI)")
            self.gui.LAI_lineEdit.setText("3")
            self.gui.CanopyMP_Box.setDisabled(False)
            self.gui.ForestMP_Box.setDisabled(True)
            self.select_background(bg_type=self.bg_type)

        if lop == "prospectD":
            self.gui.Canth_Slide.setDisabled(False)
            self.gui.Canth_lineEdit.setDisabled(False)
            self.gui.Canth_Text.setDisabled(False)

            self.gui.Cbrown_Slide.setDisabled(False)
            self.gui.Cbrown_lineEdit.setDisabled(False)
            self.gui.Cbrown_Text.setDisabled(False)

            self.gui.Car_Slide.setDisabled(False)
            self.gui.Car_lineEdit.setDisabled(False)
            self.gui.Car_Text.setDisabled(False)

            self.gui.Cp_Slide.setDisabled(True)
            self.gui.Cp_lineEdit.setDisabled(True)
            self.gui.Cp_Text.setDisabled(True)

            self.gui.Cbc_Slide.setDisabled(True)
            self.gui.Cbc_lineEdit.setDisabled(True)
            self.gui.Cbc_Text.setDisabled(True)

            self.gui.Cm_Slide.setDisabled(False)
            self.gui.Cm_lineEdit.setDisabled(False)
            self.gui.Cm_Text.setDisabled(False)

        elif lop == "prospectPro":
            self.gui.Canth_Slide.setDisabled(False)
            self.gui.Canth_lineEdit.setDisabled(False)
            self.gui.Canth_Text.setDisabled(False)

            self.gui.Cbrown_Slide.setDisabled(False)
            self.gui.Cbrown_lineEdit.setDisabled(False)
            self.gui.Cbrown_Text.setDisabled(False)

            self.gui.Car_Slide.setDisabled(False)
            self.gui.Car_lineEdit.setDisabled(False)
            self.gui.Car_Text.setDisabled(False)

            self.gui.Cp_Slide.setDisabled(False)
            self.gui.Cp_lineEdit.setDisabled(False)
            self.gui.Cp_Text.setDisabled(False)

            self.gui.Cbc_Slide.setDisabled(False)
            self.gui.Cbc_lineEdit.setDisabled(False)
            self.gui.Cbc_Text.setDisabled(False)

            self.gui.Cm_Slide.setDisabled(True)
            self.gui.Cm_lineEdit.setDisabled(True)
            self.gui.Cm_Text.setDisabled(True)

        elif lop == "prospect5B":
            self.gui.Canth_Slide.setDisabled(True)
            self.gui.Canth_lineEdit.setDisabled(True)
            self.gui.Canth_Text.setDisabled(True)

            self.gui.Cbrown_Slide.setDisabled(False)
            self.gui.Cbrown_lineEdit.setDisabled(False)
            self.gui.Cbrown_Text.setDisabled(False)

            self.gui.Car_Slide.setDisabled(False)
            self.gui.Car_lineEdit.setDisabled(False)
            self.gui.Car_Text.setDisabled(False)

            self.gui.Cp_Slide.setDisabled(True)
            self.gui.Cp_lineEdit.setDisabled(True)
            self.gui.Cp_Text.setDisabled(True)

            self.gui.Cbc_Slide.setDisabled(True)
            self.gui.Cbc_lineEdit.setDisabled(True)
            self.gui.Cbc_Text.setDisabled(True)

            self.gui.Cm_Slide.setDisabled(False)
            self.gui.Cm_lineEdit.setDisabled(False)
            self.gui.Cm_Text.setDisabled(False)

        elif lop == "prospect5":
            self.gui.Canth_Slide.setDisabled(True)
            self.gui.Canth_lineEdit.setDisabled(True)
            self.gui.Canth_Text.setDisabled(True)

            self.gui.Cbrown_Slide.setDisabled(True)
            self.gui.Cbrown_lineEdit.setDisabled(True)
            self.gui.Cbrown_Text.setDisabled(True)

            self.gui.Car_Slide.setDisabled(False)
            self.gui.Car_lineEdit.setDisabled(False)
            self.gui.Car_Text.setDisabled(False)

            self.gui.Cp_Slide.setDisabled(True)
            self.gui.Cp_lineEdit.setDisabled(True)
            self.gui.Cp_Text.setDisabled(True)

            self.gui.Cbc_Slide.setDisabled(True)
            self.gui.Cbc_lineEdit.setDisabled(True)
            self.gui.Cbc_Text.setDisabled(True)

            self.gui.Cm_Slide.setDisabled(False)
            self.gui.Cm_lineEdit.setDisabled(False)
            self.gui.Cm_Text.setDisabled(False)

        elif lop == "prospect4":
            self.gui.Canth_Slide.setDisabled(True)
            self.gui.Canth_lineEdit.setDisabled(True)
            self.gui.Canth_Text.setDisabled(True)

            self.gui.Cbrown_Slide.setDisabled(True)
            self.gui.Cbrown_lineEdit.setDisabled(True)
            self.gui.Cbrown_Text.setDisabled(True)

            self.gui.Car_Slide.setDisabled(True)
            self.gui.Car_lineEdit.setDisabled(True)
            self.gui.Car_Text.setDisabled(True)

            self.gui.Cp_Slide.setDisabled(True)
            self.gui.Cp_lineEdit.setDisabled(True)
            self.gui.Cp_Text.setDisabled(True)

            self.gui.Cbc_Slide.setDisabled(True)
            self.gui.Cbc_lineEdit.setDisabled(True)
            self.gui.Cbc_Text.setDisabled(True)

            self.gui.Cm_Slide.setDisabled(False)
            self.gui.Cm_lineEdit.setDisabled(False)
            self.gui.Cm_Text.setDisabled(False)

        self.mod_exec()

    def para_init(self):
        # Read PROSAIL variables from the lineEdits and update the para_dict dictionary
        self.select_s2s(sensor_index=0, trigger=False)  # initialize the sensor without triggering a new PROSAIL run
        self.para_dict["N"] = float(self.gui.N_lineEdit.text())
        self.para_dict["cab"] = float(self.gui.Cab_lineEdit.text())
        self.para_dict["cw"] = float(self.gui.Cw_lineEdit.text())
        self.para_dict["cm"] = float(self.gui.Cm_lineEdit.text())
        self.para_dict["LAI"] = float(self.gui.LAI_lineEdit.text())
        self.para_dict["typeLIDF"] = float(2)
        self.para_dict["LIDF"] = float(self.gui.LIDFB_lineEdit.text())
        self.para_dict["hspot"] = float(self.gui.hspot_lineEdit.text())
        self.para_dict["psoil"] = float(self.gui.psoil_lineEdit.text())
        self.para_dict["tts"] = float(self.gui.SZA_lineEdit.text())
        self.para_dict["tto"] = float(self.gui.OZA_lineEdit.text())
        self.para_dict["psi"] = float(self.gui.rAA_lineEdit.text())
        self.para_dict["cp"] = float(self.gui.Cp_lineEdit.text())
        self.para_dict["car"] = float(self.gui.Car_lineEdit.text())
        self.para_dict["anth"] = float(self.gui.Canth_lineEdit.text())
        self.para_dict["cbrown"] = float(self.gui.Cbrown_lineEdit.text())
        self.para_dict["LAIu"] = float(self.gui.LAIu_lineEdit.text())
        self.para_dict["cd"] = float(self.gui.CD_lineEdit.text())
        self.para_dict["sd"] = float(self.gui.SD_lineEdit.text())
        self.para_dict["h"] = float(self.gui.TreeH_lineEdit.text())
        self.para_dict["cbc"] = float(self.gui.Cbc_lineEdit.text())

    def mod_interactive(self):
        self.gui.N_Slide.valueChanged.connect(lambda: self.mod_exec(slider=self.gui.N_Slide, item="N"))
        self.gui.Cab_Slide.valueChanged.connect(lambda: self.mod_exec(slider=self.gui.Cab_Slide, item="cab"))
        self.gui.Cw_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.Cw_Slide, item="cw"))
        self.gui.Cm_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.Cm_Slide, item="cm"))
        self.gui.LAI_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.LAI_Slide, item="LAI"))
        self.gui.LIDFB_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.LIDFB_Slide, item="LIDF"))
        self.gui.hspot_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.hspot_Slide, item="hspot"))
        self.gui.psoil_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.psoil_Slide, item="psoil"))
        self.gui.SZA_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.SZA_Slide, item="tts"))
        self.gui.OZA_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.OZA_Slide, item="tto"))
        self.gui.rAA_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.rAA_Slide, item="psi"))
        self.gui.Cp_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.Cp_Slide, item="cp"))
        self.gui.Cbc_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.Cbc_Slide, item="cbc"))
        self.gui.Car_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.Car_Slide, item="car"))
        self.gui.Canth_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.Canth_Slide, item="anth"))
        self.gui.Cbrown_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.Cbrown_Slide, item="cbrown"))
        self.gui.LAIu_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.LAIu_Slide, item="LAIu"))
        self.gui.SD_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.SD_Slide, item="sd"))
        self.gui.TreeH_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.TreeH_Slide, item="h"))
        self.gui.CD_Slide.valueChanged.connect(lambda: self.mod_exec(self.gui.CD_Slide, item="cd"))

        self.gui.B_DefSoilSpec.clicked.connect(lambda: self.select_background(bg_type="default"))
        self.gui.B_LoadBackSpec.clicked.connect(lambda: self.select_background(bg_type="load"))
        self.gui.B_LoadBackSpec.pressed.connect(lambda: self.select_background(bg_type="load"))

        self.gui.LIDF_combobox.currentIndexChanged.connect(self.select_LIDF)
        self.gui.SType_combobox.currentIndexChanged.connect(
            lambda: self.select_s2s(sensor_index=self.gui.SType_combobox.currentIndex()))  # Sensor Type combobox

        self.gui.CheckPlotAcc.stateChanged.connect(lambda: self.txtColorBars())
        self.gui.pushClearPlot.clicked.connect(
            lambda: self.clear_plot(rescale=True, clear_plots=True))  # clear the plot canvas
        self.gui.cmdResetScale.clicked.connect(lambda: self.clear_plot(rescale=True, clear_plots=False))
        self.gui.Push_LoadInSitu.clicked.connect(
            lambda: self.open_file(open_type="in situ"))  # load own in situ spectrum
        self.gui.push_SelectFile.clicked.connect(
            lambda: self.open_file(open_type="background"))  # load own background spec

        self.gui.Push_Exit.clicked.connect(self.gui.accept)  # exit app
        self.gui.Push_ResetInSitu.clicked.connect(self.reset_in_situ)  # remove own spectrum from plot canvas

        self.gui.Push_SaveSpec.clicked.connect(self.save_spectrum)
        self.gui.Push_SaveParams.clicked.connect(self.save_paralist)

        self.gui.lblFake.setVisible(False)  # placeholder for typeLIDF object in coloring

    def txtColorBars(self):
        # Colorbars in the lineEdits help the user identify which spectrum was triggered by which variable change
        if self.gui.CheckPlotAcc.isChecked():  # show color spots only when accumulative plotting is activated
            for i, lineEdit in enumerate(self.lineEdits):
                color_str = "rgb%s" % str(self.colors[i])
                # style of the lineEdits are specified by StyleSheets
                # the background-color is defined by pseudo-gradients that turn into discrete areas with
                # white from 0 to 0.849 (left 85 % of the lineEdit) and the individual color from 85 to 100 %
                lineEdit.setStyleSheet("""background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                stop:0 rgb(255, 255, 255), stop:0.849 rgb(255, 255, 255),
                stop:0.85 %s, stop:1 %s);""" % (color_str, color_str))
        else:
            for lineEdit in self.lineEdits:
                lineEdit.setStyleSheet("background - color: rgb(255, 255, 255);")

    def mod_exec(self, slider=None, item=None):
        # this function is called whenever PROSAIL is to be triggered; it is the function to sort all inputs and
        # call PROSAIL with the selected settings

        if slider is not None and item is not None:
            self.para_dict[item] = slider.value() / 10000.0  # update para_list

        # create new Instance of the RTM
        mod_I = mod.InitModel(lop=self.lop, canopy_arch=self.canopy_arch, nodat=-999, int_boost=1.0, s2s=self.sensor)
        # initialize a single model run (as opposed to a vectorized run which is used for LUT-creation)
        self.myResult = mod_I.initialize_single(tts=self.para_dict["tts"],
                                                tto=self.para_dict["tto"],
                                                psi=self.para_dict["psi"],
                                                N=self.para_dict["N"],
                                                cab=self.para_dict["cab"],
                                                cw=self.para_dict["cw"],
                                                cm=self.para_dict["cm"],
                                                LAI=self.para_dict["LAI"],
                                                LIDF=self.para_dict["LIDF"],
                                                typeLIDF=self.para_dict["typeLIDF"],
                                                hspot=self.para_dict["hspot"],
                                                psoil=self.para_dict["psoil"],
                                                cp=self.para_dict["cp"],
                                                cbc=self.para_dict["cbc"],
                                                car=self.para_dict["car"],
                                                cbrown=self.para_dict["cbrown"],
                                                anth=self.para_dict["anth"],
                                                soil=self.bg_spec,
                                                LAIu=self.para_dict["LAIu"],
                                                cd=self.para_dict["cd"],
                                                sd=self.para_dict["sd"],
                                                h=self.para_dict["h"])[0, :]

        if item is not None:
            self.item = item

        self.plotting()

    def plotting(self):
        # handles the plotting of the PROSAIL result
        if not self.gui.CheckPlotAcc.isChecked():  # if accumulative plotting is NOT active
            self.mPlotItems.clear()  # delete the existing plot
            r = self.gui.graphicsView.plot(self.wl, self.myResult, clear=True, pen="g", fillLevel=0,
                                           fillBrush=(255, 255, 255, 30),
                                           name='modelled')
            self.mPlotItems.append(r)
            self.gui.graphicsView.setLabel('left', text="Reflectance [%]")
            self.gui.graphicsView.setLabel('bottom', text="Wavelength [nm]")

        else:  # accumulative plotting is active
            try:
                myPen = pg.mkPen(color=self.colors_dict[self.item], style=self.penStyle)  # define the pen style
            except KeyError:  # This happens when sensor is chosen before parameter, set to "green" per default then
                myPen = pg.mkPen(color=self.colors_dict["cab"], style=self.penStyle)
            r = self.gui.graphicsView.plot(self.wl, self.myResult, pen=myPen)
            self.mPlotItems.append(r)
            self.plot_own_spec()  # add the in-situ spectrum if available
            self.gui.graphicsView.setLabel('left', text="Reflectance [%]")
            self.gui.graphicsView.setLabel('bottom', text="Wavelength [nm]")

        if self.data_mean is not None and not self.gui.CheckPlotAcc.isChecked():
            self.plot_own_spec()  # add the in-situ spectrum if available

            # calculate statistics for a comparison between in situ spectrum and PROSAIL output
            # Use np.nansums as spectra may contain np.nans which would cause wrong results
            try:
                # Mean Absolute Error
                mae = np.nansum(abs(self.myResult - self.data_mean)) / len(self.myResult)

                # Root Mean Squared Error
                rmse = np.sqrt(np.nanmean((self.myResult - self.data_mean) ** 2))

                # Nash-Sutcliffe Efficiency Error
                nse = 1.0 - ((np.nansum((self.data_mean - self.myResult) ** 2)) /
                             (np.nansum((self.data_mean - (np.nanmean(self.data_mean))) ** 2)))

                # Modified Nash-Sutcliffe Efficiency Error
                mnse = 1.0 - ((np.nansum(abs(self.data_mean - self.myResult))) /
                              (np.nansum(abs(self.data_mean - (np.nanmean(self.data_mean))))))

                # R²
                r_squared = ((np.nansum(
                    (self.data_mean - np.nanmean(self.data_mean)) * (self.myResult - np.nanmean(self.myResult))))
                             / ((np.sqrt(np.nansum((self.data_mean - np.nanmean(self.data_mean)) ** 2)))
                                * (np.sqrt(np.nansum((self.myResult - np.nanmean(self.myResult)) ** 2))))) ** 2

                # Add the errors to the plot
                errors = pg.TextItem("RMSE: %.4f" % rmse +
                                     "\nMAE: %.4f" % mae +
                                     "\nNSE: %.4f" % nse +
                                     "\nmNSE: %.2f" % mnse +
                                     '\n' + u'R²: %.2f' % r_squared, (100, 200, 255),
                                     border="w", anchor=(1, 0))
            except:
                errors = pg.TextItem("RMSE: sensors mismatch" +
                                     "\nMAE: sensors mismatch " +
                                     "\nNSE: sensors mismatch" +
                                     "\nmNSE: sensors mismatch" +
                                     '\n' + u'R²: sensors mismatch ', (100, 200, 255),
                                     border="w", anchor=(1, 0))
            errors.setPos(2500, 0.55)
            self.mPlotItems.append(errors)
            self.gui.graphicsView.addItem(errors)

    def open_file(self, open_type):
        self.main.loadtxtfile.open(type=open_type)

    def open_sensoreditor(self):
        self.main.sensoreditor.open()

    def reset_in_situ(self):
        self.data_mean = None
        self.mod_exec()

    def plot_own_spec(self):
        if self.data_mean is not None:
            r = self.gui.graphicsView.plot(self.wl_open, self.data_mean, name='observed')
            self.mPlotItems.append(r)

    def clear_plot(self, rescale=False, clear_plots=False):
        if rescale:
            self.gui.graphicsView.setYRange(0, 1, padding=0)
            self.gui.graphicsView.setXRange(350, 2550, padding=0)

        if clear_plots:
            self.gui.graphicsView.clear()
            self.plot_count = 0

    def save_spectrum(self):
        # saves the current spectrum as a textfile with two columns (wavelength and reflectances)
        specnameout = QFileDialog.getSaveFileName(caption='Save Modelled Spectrum',
                                                  filter="Text files (*.txt)")
        if not specnameout:
            return
        save_matrix = np.zeros(shape=(len(self.wl), 2))
        save_matrix[:, 0] = self.wl
        save_matrix[:, 1] = self.myResult

        np.savetxt(specnameout[0], save_matrix, delimiter="\t", header="Wavelength_nm\tReflectance")

    def save_paralist(self):
        # saves the current parameters to file with two columns (parameter name and value)
        paralistout = QFileDialog.getSaveFileName(caption='Save Modelled Spectrum Parameters',
                                                  filter="Text files (*.txt)")
        if paralistout:
            with open(paralistout[0], "w") as file:
                for para_key in self.para_dict:
                    if self.lineEdits_dict[para_key].isEnabled():
                        file.write("%s\t%f\n" % (para_key, self.para_dict[para_key]))
            file.close()


# Class SensorEditor allows to create new .srf from text files or imagery that contain srf-information
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
        #
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
        elif not self.main.ivvrm.gui.SType_combobox.findText(sensor_name) == -1:
            self.houston(message="A sensor with this name already exists in the list!", disable_cmdOK=False)
            return
        if self.flag_srf and self.flag_wl and not self.flag_image:
            # A numpy array file is created from the sensor srf files and the wavelength file
            # it is first saved as .npz format and renamed to .srf afterwards
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
            self.main.ivvrm.init_sensorlist()
            # set index of the combobox to new sensor
            sensor_index = self.main.ivvrm.gui.SType_combobox.findText(sensor_name)
            if sensor_index >= 0:  # sensor_index is -1 if the sensor creation failed; in this case, don't update sensor
                self.main.ivvrm.gui.SType_combobox.setCurrentIndex(sensor_index)
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
                self.main.ivvrm.init_sensorlist()


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
        self.gui.cmbDelimiter.activated.connect(
            lambda: self.change_cmbDelimiter())  # "activated" signal is only called for user activity, not code call
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
        self.open_type = type  # type is either "in situ" or "background", this changes the design of the GUI
        self.gui.setWindowTitle("Open %s Spectrum" % type)
        self.gui.show()

    def open_file(self):
        file_choice, _filter = QFileDialog.getOpenFileName(None, 'Select Spectrum File',
                                                           APP_DIR + "/Resources/Example_Files", "(*.txt *.csv)")
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
            raw_file.seek(0)
            raw = csv.reader(raw_file, self.dialect)
            try:
                # if the first row can be converted to int, it most likely does not contain a header
                _ = int(next(raw)[0])
                self.header_bool = False
            except:
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

        wl_offset = 400 - int(self.wl_open[0])  # PROSAIL wavelengths start at 400, consider an offset if necessary)

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
            item = QTableWidgetItem(str(self.data_mean[row]))
            self.gui.tablePreview.setItem(row, 0, item)

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
        self.main.ivvrm.wl_open = self.wl_open  # communicate with th IVVRM GUI class to pass the wavelengths
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
        self.default_exclude = [i for j in (range(960, 1021), range(1390, 1551), range(2000, 2101)) for i in j]

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

        # if the spectra are of type "in situ", the excluded bands are set to np.nan
        if self.main.loadtxtfile.open_type == "in situ":
            self.main.ivvrm.data_mean = np.asarray([self.main.loadtxtfile.data_mean[i] if i not in exclude_bands
                                                    else np.nan for i in range(len(self.main.loadtxtfile.data_mean))])

        # if spectra are of type "background", single bands are converted to ranges in which spectra are interpolated
        elif self.main.loadtxtfile.open_type == "background":
            water_absorption_ranges = self.generate_ranges(range_list=exclude_bands)

            # the following loop iterates over all ranges of excluded bands (e.g absorption ranges of atm. water vap.)
            # and performs a simple linear interpolation in between to overwrite the actual signal
            # y is the data from the textfile in the exclude ranges
            # f is the interpolated representation
            for interp_bands in water_absorption_ranges:
                y = [self.main.loadtxtfile.data_mean[interp_bands[0]],
                     self.main.loadtxtfile.data_mean[interp_bands[-1]]]
                f = interp1d([interp_bands[0], interp_bands[-1]], [y[0], y[1]])
                self.main.loadtxtfile.data_mean[interp_bands[1:-1]] = f(interp_bands[1:-1])

            # set the bg_spec to the reflectances of the text file with the interpolated ranges
            self.main.ivvrm.bg_spec = self.main.loadtxtfile.data_mean
            self.main.ivvrm.gui.BackSpec_label.setText(os.path.basename(self.main.loadtxtfile.filenameIn))
            self.main.ivvrm.gui.push_SelectFile.setEnabled(False)
            self.main.ivvrm.gui.push_SelectFile.setText('File:')

        # clean up
        for list_object in [self.gui.lstIncluded, self.gui.lstExcluded]:
            list_object.clear()

        self.main.ivvrm.mod_exec()
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


# class MainUiFunc is the interface between all sub-guis, so they can communicate between each other
class MainUiFunc:
    def __init__(self):
        self.QGis_app = QApplication.instance()  # the QGIS-Application is made accessible within the code
        self.ivvrm = IVVRM(self)
        # self.ivvrm_exec = StartIVVRM(self)
        self.loadtxtfile = LoadTxtFile(self)
        self.sensoreditor = SensorEditor(self)
        self.select_wavelengths = SelectWavelengths(self)

    def show(self):
        self.ivvrm.gui.show()


if __name__ == '__main__':
    from enmapbox.testing import start_app

    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())
