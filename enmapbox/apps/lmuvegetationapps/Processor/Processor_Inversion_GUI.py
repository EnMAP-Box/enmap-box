# -*- coding: utf-8 -*-
"""
***************************************************************************
    Processor_Inversion_core.py - LMU Agri Apps - Artificial Neural Network based spectroscopic image inversion of
    PROSAIL parameters - GUI
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

This script handles the GUI for inverting images with pre-trained Machine Learning models. At the time being, only
ANNs are implemented, but the structure is flexible so that new algorithms can always be added. Make sure to
add a model selection frame to the GUI in QtDesigner then.

"""
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel

import sys
import os
# ensure to call QGIS before PyQtGraph
from qgis.PyQt.QtWidgets import *
import lmuvegetationapps.Processor.Processor_Inversion_core as processor
from lmuvegetationapps import APP_DIR
from _classic.hubflow.core import *
from enmapbox.gui.utils import loadUi

pathUI_processor = os.path.join(APP_DIR, 'Resources/UserInterfaces/Processor_Inversion.ui')
pathUI_nodat = os.path.join(APP_DIR, 'Resources/UserInterfaces/Nodat.ui')
pathUI_prgbar = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')


class MLInversionGUI(QDialog):
    
    def __init__(self, parent=None):
        mLayerImage: QgsMapLayerComboBox
        mLayerGeometry: QgsMapLayerComboBox
        mLayerMask: QgsMapLayerComboBox
        super(MLInversionGUI, self).__init__(parent)
        loadUi(pathUI_processor, self)
        self.mLayerImage.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mLayerGeometry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mLayerMask.setFilters(QgsMapLayerProxyModel.RasterLayer)


class NodatGUI(QDialog):

    def __init__(self, parent=None):
        super(NodatGUI, self).__init__(parent)
        loadUi(pathUI_nodat, self)


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


# class MachineLearningInversion (MLInversion)
# This is the GUI class for setting up and performing an inversion of machine learning models
class MLInversion:

    def __init__(self, main):
        self.main = main
        self.gui = MLInversionGUI()
        self.initial_values()
        self.connections()

    def initial_values(self):
        self.nodat = [-999] * 3
        self.image = None  # Spectral Image to be inverted
        self.mask_image = None  # Boolean mask image (0 and 1) to set pixels to add or remove from the inversion
        self.mask_ndvi = False  # Boolean: True, only invert pixels with NDVI > self.ndvi_thr; False: invert all pixels
        self.ndvi_thr = -0.9
        self.ndvi_bands = [None, None]
        # should each pixel be inverted according to its geometry (True) or calculate the average for all pixels (False)
        self.spatial_geo = False  #
        self.out_image = None  # File for output results
        self.out_mode = 'single'  # 'single' all PROSAIL parameters in one file as bands, 'individual' one file per para

        self.geo_mode = "file"  # Is the geometry (SZA, OZA, rAA) suplied through 'file' or are they 'fix'
        self.geo_file = None  # if geo_mode == 'file', which is the path?
        self.geo_fixed = [None]*3  # if geo_mode == 'fix', which are the three geometry angles?

        self.conversion_factor = None  # convert spectral image (boost) to reach the same scale as the machines

        self.addItemImage, self.addItemGeometry, self.addItemMask = ([], [], [])
        self.gui.mLayerImage.setLayer(None)
        self.gui.mLayerGeometry.setLayer(None)
        self.gui.mLayerMask.setLayer(None)

        self.algorithm = None

        # Initial Model is set to EnMAP as default
        self.model_meta_file = os.path.join(APP_DIR, 'Resources/Processor/EnMAP.meta')
        self.meta_dict = self._get_processor_meta(file=self.model_meta_file)
        if not self.meta_dict:
            return
        self.model_name = os.path.splitext(os.path.basename(self.model_meta_file))[0]
        # The name of the meta-file == name of the model
        self.gui.lblModel.setText(os.path.splitdrive(self.model_meta_file)[0] + "\\...\\" + self.model_name + ".meta")

    def connections(self):
        # Model Selection
        self.gui.cmdModel.clicked.connect(lambda: self.open_file(mode="model"))

        # Switch to "Train new Model"
        self.gui.cmdNewModel.clicked.connect(lambda: self.open_train_gui())

        # Input Images
        self.gui.mLayerImage.layerChanged.connect(lambda: self.open_file(mode="imgDropdown"))
        self.gui.cmdInputImage.clicked.connect(lambda: self.open_file(mode="imgSelect"))
        self.gui.mLayerMask.layerChanged.connect(lambda: self.open_file(mode="maskDropdown"))
        self.gui.cmdInputMask.clicked.connect(lambda: self.open_file(mode="maskSelect"))

        # Output Images
        self.gui.cmdOutputImage.clicked.connect(lambda: self.open_file(mode="output"))
        self.gui.radOutSingle.clicked.connect(lambda: self.select_outputmode(mode="single"))
        self.gui.radOutIndividual.clicked.connect(lambda: self.select_outputmode(mode="individual"))

        # Geometry
        self.gui.mLayerGeometry.layerChanged.connect(lambda: self.open_file(mode="geoDropdown"))
        self.gui.cmdGeoFromFile.clicked.connect(lambda: self.open_file(mode="geoSelect"))
        self.gui.radGeoFromFile.clicked.connect(lambda: self.select_geo(mode="file"))
        self.gui.radGeoFix.clicked.connect(lambda: self.select_geo(mode="fix"))

        self.gui.grpNDVI.clicked.connect(lambda: self.ndvi_thresh())
        self.gui.SpinNDVI.valueChanged.connect(lambda: self.ndvi_th_change())

        self.gui.chkMeanCalc.clicked.connect(lambda: self.geo_mean_calc())

        # Execute
        self.gui.cmdRun.clicked.connect(lambda: self.run_inversion())
        self.gui.cmdClose.clicked.connect(lambda: self.gui.close())

    def open_file(self, mode):
        if mode == "imgSelect":
            if self.image is not None:
                self.image = None
            bsq_input = QFileDialog.getOpenFileName(caption='Select Input Image', filter="ENVI Image (*.bsq)")[0]
            if not bsq_input:
                return
            self.addItemImage.append(bsq_input)
            self.gui.mLayerImage.setAdditionalItems(self.addItemImage)
            self.gui.mLayerImage.setCurrentText(bsq_input)

            self.image = bsq_input
            try:
                meta = self.get_image_meta(image=self.image, image_type="Input Image")  # get metadata of image
            except ValueError as e:
                self.abort(message=str(e))
                return
            if None in meta:
                self.image = None
                self.nodat[0] = None
                return
            else:
                self.gui.lblNodatImage.setText(str(meta[0]))
                self.gui.txtNodatOutput.setText(str(meta[0]))
                self.nodat[0] = meta[0]

        elif mode == "imgDropdown":
            if self.image is not None:
                self.image = None
            if self.gui.mLayerImage.currentLayer() is not None:
                input = self.gui.mLayerImage.currentLayer()
                bsq_input = input.source()
            elif len(self.gui.mLayerImage.currentText()) > 0:
                bsq_input = self.gui.mLayerImage.currentText()
            else:
                self.image = None
                return
            self.image = bsq_input
            try:
                meta = self.get_image_meta(image=self.image, image_type="Input Image")  # get metadata of image
            except ValueError as e:
                self.abort(message=str(e))
                return
            if None in meta:
                self.image = None
                self.nodat[0] = None
                return
            else:
                self.gui.lblNodatImage.setText(str(meta[0]))
                self.gui.txtNodatOutput.setText(str(meta[0]))
                self.nodat[0] = meta[0]

        elif mode == "output":
            result = QFileDialog.getSaveFileName(caption='Specify Output File',
                                                 filter="ENVI Image (*.bsq)")[0]
            self.out_path = result
            self.out_path = self.out_path.replace("\\", "/")
            self.gui.txtOutputImage.setText(result)

        elif mode == "lut":  # file open is a lut-metafile
            result = str(QFileDialog.getOpenFileName(caption='Select LUT meta-file', filter="LUT-file (*.lut)")[0])
            if not result:
                return
            self.lut_path = result
            self.gui.lblInputLUT.setText(result)
            with open(self.lut_path, 'r') as metafile:
                metacontent = metafile.readlines()
                metacontent = [line.rstrip('\n') for line in metacontent]
            if metacontent[4].split("=")[1] == "None":  # if LUT is Prospect only (no canopy_arch), disable geos
                self.gui.radGeoFix.setDisabled(True)
                self.gui.radGeoFromFile.setDisabled(True)
                self.gui.radGeoOff.setChecked(True)
                self.select_geo(mode="off")
            else:
                self.gui.radGeoFix.setDisabled(False)
                self.gui.radGeoFromFile.setDisabled(False)

        elif mode == "geoSelect":  # open file is a geometry file
            result = str(QFileDialog.getOpenFileName(caption='Select Geometry Image')[0])
            if not result:
                return
            self.geo_file = result
            meta = self.get_image_meta(image=self.geo_file, image_type="Geometry Image")
            if None in meta:
                self.geo_file = None
                self.nodat[1] = -999
                return
            else:
                self.gui.lblNodatGeoImage.setText(str(meta[0]))
                self.gui.chkMeanCalc.setDisabled(False)
                self.gui.chkMeanCalc.setChecked(True)
                self.nodat[1] = meta[0]

                self.addItemGeometry.append(result)
                self.gui.mLayerGeometry.setAdditionalItems(self.addItemGeometry)
                self.gui.mLayerGeometry.setCurrentText(result)

        elif mode == "geoDropdown":
            if self.geo_file is not None:
                self.geo_file = None
            if self.gui.mLayerGeometry.currentLayer() is not None:
                ginput = self.gui.mLayerGeometry.currentLayer()
                geo_input = ginput.source()
            elif len(self.gui.mLayerGeometry.currentText()) > 0:
                geo_input = self.gui.mLayerGeometry.currentText()
            else:
                self.geo_file = None
                return
            self.geo_file = geo_input
            meta = self.get_image_meta(image=self.geo_file, image_type="Geometry Image")
            if None in meta:
                self.geo_file = None
                self.nodat[1] = -999
                return
            else:
                self.gui.lblNodatGeoImage.setText(str(meta[0]))
                self.gui.chkMeanCalc.setDisabled(False)
                self.gui.chkMeanCalc.setChecked(True)
                self.nodat[1] = meta[0]

        elif mode == "maskSelect":  # open file of type mask image (0 and 1)
            result = str(QFileDialog.getOpenFileName(caption='Select Mask Image')[0])
            if not result:
                return
            self.mask_image = result
            meta = self.get_image_meta(image=self.mask_image, image_type="Mask Image")
            if meta[1] is None:  # No Data is unimportant for mask file, but dimensions must exist (image readable)
                self.mask_image = None
                return
            else:
                self.addItemMask.append(result)
                self.gui.mLayerMask.setAdditionalItems(self.addItemMask)
                self.gui.mLayerMask.setCurrentText(result)

        elif mode == "maskDropdown":
            if self.mask_image is not None:
                self.mask_image = None
            if self.gui.mLayerMask.currentLayer() is not None:
                minput = self.gui.mLayerMask.currentLayer()
                mask_input = minput.source()
            elif len(self.gui.mLayerMask.currentText()) > 0:
                mask_input = self.gui.mLayerMask.currentText()
            else:
                self.mask_image = None
                return
            self.mask_image = mask_input
            meta = self.get_image_meta(image=self.mask_image, image_type="Mask Image")
            if meta[1] is None:  # No Data is unimportant for mask file, but dimensions must exist (image readable)
                self.mask_image = None
                return

        elif mode == "model":  # Select algorithm for inversion by picking its Meta-file (*.meta)
            result = str(QFileDialog.getOpenFileName(caption='Select Machine Learning Model',
                                                     filter="Processor META File (*.meta)")[0])
            if not result:
                return
            self.meta_dict = self._get_processor_meta(file=result)
            self.algorithm = self.meta_dict['alg']

            targets = self.meta_dict.get('target_parameters')
            if isinstance(targets, str):
                self.gui.lblTargets.setText(targets)
            else:
                self.gui.lblTargets.setText(', '.join(self.meta_dict['target_parameters']))

            if not self.meta_dict:
                return
            self.model_meta_file = result
            self.model_name = os.path.splitext(os.path.basename(result))[0]
            # The name of the meta-file == name of the model
            self.gui.lblModel.setText(os.path.splitdrive(result)[0] + "\\...\\" + self.model_name + ".meta")

    def open_file_old(self, mode):
        if mode == "image":  # open file is a spectral image
            result = str(QFileDialog.getOpenFileName(caption='Select Input Image')[0])
            if not result:
                return
            self.image = result
            self.image = self.image.replace("\\", "/")
            try:
                meta = self.get_image_meta(image=self.image, image_type="Input Image")  # get metadata of image
            except ValueError as e:
                self.abort(message=str(e))
                return
            if None in meta[:-1]:  # something went wrong, go back to default (last item is NDVI which is optional)
                self.image = None
                self.nodat[0] = None
                self.gui.lblInputImage.setText("")
                return
            else:
                self.gui.lblInputImage.setText(result)
                self.gui.lblNodatImage.setText(str(meta[0]))
                self.nodat[0] = meta[0]

        elif mode == "output":  # open file for output raster
            result = QFileDialog.getSaveFileName(caption='Specify Output-file(s)', filter="ENVI Image (*.bsq)")[0]
            if not result:
                return
            self.out_image = result
            self.out_image = self.out_image.replace("\\", "/")
            self.gui.txtOutputImage.setText(result)

        elif mode == "geo":  # open file is a geometry file
            result = str(QFileDialog.getOpenFileName(caption='Select Geometry Image')[0])
            if not result:
                return
            self.geo_file = result
            self.geo_file = self.geo_file.replace("\\", "/")
            meta = self.get_image_meta(image=self.geo_file, image_type="Geometry Image")
            if None in meta:
                self.geo_file = None
                self.nodat[1] = None
                self.gui.lblGeoFromFile.setText("")
                return
            else:
                self.gui.lblGeoFromFile.setText(result)
                self.gui.lblNodatGeoImage.setText(str(meta[0]))
                self.gui.chkMeanCalc.setDisabled(False)
                self.gui.chkMeanCalc.setChecked(True)
                self.nodat[1] = meta[0]

        elif mode == "mask":  # open file of type mask image (0 and 1)
            result = str(QFileDialog.getOpenFileName(caption='Select Mask Image')[0])
            if not result:
                return
            self.mask_image = result
            self.mask_image = self.mask_image.replace("\\", "/")
            meta = self.get_image_meta(image=self.mask_image, image_type="Mask Image")
            if meta[1] is None:  # No Data is unimportant for mask file, but dimensions must exist (image readable)
                self.mask_image = None
                self.gui.lblInputMask.setText("")
                return
            else:
                self.gui.lblInputMask.setText(result)

        elif mode == "model":  # Select algorithm for inversion by picking its Meta-file (*.meta)
            result = str(QFileDialog.getOpenFileName(caption='Select Machine Learning Model',
                                                     filter="Processor META File (*.meta)")[0])
            if not result:
                return
            self.meta_dict = self._get_processor_meta(file=result)
            if not self.meta_dict:
                return
            self.model_meta_file = result
            self.model_name = os.path.splitext(os.path.basename(result))[0]
            # The name of the meta-file == name of the model
            self.gui.lblModel.setText(os.path.splitdrive(result)[0] + "\\...\\" + self.model_name + ".meta")

    def select_outputmode(self, mode):  # 'single' vs. 'individual'
        self.out_mode = mode

    def select_geo(self, mode):
        # sets objects in the GUI according to the Geo-mode: is geometry read from file or fixed manually?
        if mode == "file":
            self.gui.chkMeanCalc.setDisabled(False)
            self.gui.mLayerGeometry.setDisabled(False)
            self.gui.cmdGeoFromFile.setDisabled(False)
            self.gui.txtSZA.setDisabled(True)
            self.gui.txtOZA.setDisabled(True)
            self.gui.txtRAA.setDisabled(True)
        if mode == "fix":
            self.gui.chkMeanCalc.setDisabled(True)
            self.gui.mLayerGeometry.setDisabled(True)
            self.gui.mLayerGeometry.setLayer(None)
            self.gui.cmdGeoFromFile.setDisabled(True)
            self.gui.txtSZA.setDisabled(False)
            self.gui.txtOZA.setDisabled(False)
            self.gui.txtRAA.setDisabled(False)
        self.geo_mode = mode

    def ndvi_thresh(self):
        # Select threshold of NDVI
        if self.gui.grpNDVI.isChecked():
            self.gui.SpinNDVI.setDisabled(False)
            self.mask_ndvi = True
        else:
            self.gui.SpinNDVI.setDisabled(True)
            self.mask_ndvi = False

    def ndvi_th_change(self):
        self.ndvi_thr = self.gui.SpinNDVI.value()

    def geo_mean_calc(self):
        if self.gui.chkMeanCalc.isChecked():
            self.spatial_geo = False
        else:
            self.spatial_geo = True

    def abort(self, message):
        QMessageBox.critical(self.gui, "Error", message)

    def check_and_assign(self):
        # Model Dir
        if self.model_meta_file is None:
            raise ValueError('No Model selected')

        # Image In
        if self.image is None:
            raise ValueError('Input Image missing')
        elif not os.path.isfile(self.image):
            raise ValueError('Input Image does not exist')

        # Output path
        self.out_image = self.gui.txtOutputImage.text()
        self.out_image = self.out_image.replace("\\", "/")
        if self.out_image is None:
            raise ValueError('Output file missing')
        else:
            # if user typed a file extension for the binary raster file, nothing happens; otherwise .bsq is added
            try:
                os.path.splitext(self.out_image)[1]
            except IndexError:
                self.out_image += ".bsq"

        # Geometry file:
        if self.geo_mode == "file":
            if self.geo_file is None:
                raise ValueError('Geometry-Input via file selected, but no file specified')
            elif not os.path.isfile(self.geo_file):
                raise ValueError('Geometry-Input file does not exist')
            elif self.nodat[1] >= 0:
                raise ValueError('NoData value for Geometry needs to be < 0 to avoid confusion with valid angles')

        elif self.geo_mode == "fix":
            self.gui.chkMeanCalc.setDisabled(True)
            if self.gui.txtSZA.text() == "" or self.gui.txtOZA.text() == "" or self.gui.txtRAA.text() == "":
                raise ValueError('Geometry-Input via fixed values selected, but angles are incomplete')
            elif not 0 <= float(self.gui.txtSZA.text()) <= 89:
                raise ValueError('SZA out of range [0-89]')
            elif not 0 <= float(self.gui.txtOZA.text()) <= 89:
                raise ValueError('OZA out of range [0-89]')
            elif not 0 <= int(self.gui.txtRAA.text()) <= 180:
                raise ValueError('rAA out of range [0-180]')
            else:
                try:
                    self.geo_fixed = [float(self.gui.txtSZA.text()),
                                      float(self.gui.txtOZA.text()),
                                      float(self.gui.txtRAA.text())]
                except ValueError:
                    raise ValueError('Cannot interpret Geometry angles as numbers')

        # Mask
        if self.mask_image:
            if not os.path.isfile(self.mask_image):
                raise ValueError('Mask Image does not exist')

        if self.gui.txtNodatOutput.text() == "":
            raise ValueError('Please specify no data value for output')
        else:
            # Set the NodataValue for the mask
            try:
                self.nodat[2] = int(self.gui.txtNodatOutput.text())
            except ValueError:
                raise ValueError('%s is not a valid no data value for output' % self.gui.txtNodatOutput.text())

        # Parameters to invert
        self.paras = self.meta_dict.get('target_parameters', [])

        if isinstance(self.paras, str):
            self.paras = [self.paras]
        # if self.gui.checkLAI.isChecked():
        #     self.paras.append("LAI")
        # if self.gui.checkALIA.isChecked():
        #     self.paras.append("LIDF")
        # if self.gui.checkCab.isChecked():
        #     self.paras.append("cab")
        # if self.gui.checkCm.isChecked():
        #     self.paras.append("cm")
        # if not self.paras:
        #     raise ValueError("At least one parameter needs to be selected!")

    def get_image_meta(self, image, image_type):
        # extracts meta information from the spectral image
        dataset = openRasterDataset(image)
        if dataset is None:
            raise ValueError(
                '{} could not be read. Please make sure it is a valid ENVI image'.format(image_type))
        else:
            metadict = dataset.metadataDict()

            nrows = int(metadict['ENVI']['lines'])
            ncols = int(metadict['ENVI']['samples'])
            nbands = int(metadict['ENVI']['bands'])

            try:  # try and get no data value and convert it to integer
                nodata = int(metadict['ENVI']['data ignore value'])
            except:
                # no dat not found or cannot be interpreted as intereg! No worries, the user can add it manually!
                self.main.nodat_widget.init(image_type=image_type, image=image)
                self.main.nodat_widget.gui.setModal(True)  # parent window is blocked
                self.main.nodat_widget.gui.exec_()  # unlike .show(), .exec_() waits with execution of the code,
                                                    # until the app is closed
                nodata = self.main.nodat_widget.nodat

            # When opening a spectral input image, wavelengths must be extracted from the header to find out the
            # NDVI bands for masking pixels with NDVI < threshold
            if image_type == "Input Image":
                try:
                    wavelengths = metadict['ENVI']['wavelength']
                    wl_units = metadict['ENVI']['wavelength units']
                    if wl_units.lower() in ['nanometers', 'nm', 'nanometer']:  # any of these is accepted
                        wave_convert = 1  # factor is 1, as the method expects nm anyway
                    elif wl_units.lower() in ['micrometers', 'µm', 'micrometer']:
                        wave_convert = 1000  # factor is 1000 to obtain nm
                    else:
                        raise ValueError
                    wavelengths = np.asarray([float(wl * wave_convert) for wl in wavelengths])
                    self.ndvi_bands[0] = np.argmin(np.abs(wavelengths - 677))  # find band that is closest to "red"
                    self.ndvi_bands[1] = np.argmin(np.abs(wavelengths - 837))  # find band that is closest to "nir"
                    self.gui.grpNDVI.setEnabled(True)  # make NDVI section available
                    self.gui.SpinNDVI.setEnabled(True)  # make NDVI threshold SpinBox available
                    # reset the objects/values to the current ones
                    self.ndvi_thresh()
                    self.ndvi_th_change()

                # wavelength or wavelength unit are not found as item in the header or they cannot be read properly
                except (KeyError, ValueError):
                    # Pop up a warning and disable NDVI spins
                    QMessageBox.warning(self.gui, "Warning", '{}: file has missing or corrupt wavelengths and '
                                                             'wavelength unit in header. NDVI-masking is disabled!'
                                                             .format(image))
                    self.gui.grpNDVI.setChecked(False)  # disable the option to select NDVI
                    self.gui.grpNDVI.setDisabled(True)
                    self.gui.SpinNDVI.setDisabled(True)  # disable the option to set NDVI threshold
                    # reset the objects/values to the current ones
                    self.ndvi_thresh()
                    self.ndvi_th_change()
                    self.mask_ndvi = False
                    self.ndvi_bands = [None, None]

            return nodata, nbands, nrows, ncols

    @staticmethod
    def _get_processor_meta(file):
        # reads the ML meta file and extracts the values
        try:
            with open(file, 'r') as meta_file:
                content = meta_file.readlines()
                content = [item.rstrip("\n") for item in content]
            # Super fancy! This splits the keys and values in the meta file and extracts the values separated by ";"
            keys, values = list(), list()
            [[x.append(y) for x, y in zip([keys, values], line.split(sep="=", maxsplit=1))] for line in content]
            values = [value.split(';') if ';' in value else value for value in values]
            meta_dict = dict(zip(keys, values))  # dictionary for they keys and values of the ML-meta file
            return meta_dict
        except:
            return False

    def run_inversion(self):
        try:
            self.check_and_assign()
        except ValueError as e:
            self.abort(message=str(e))
            return

        self.prg_widget = self.main.prg_widget
        self.prg_widget.gui.lblCaption_l.setText("ML Inversion")
        self.prg_widget.gui.lblCaption_r.setText("Setting up inversion...")
        self.main.prg_widget.gui.prgBar.setValue(0)
        self.main.prg_widget.gui.setModal(True)
        self.prg_widget.gui.show()

        self.main.qgis_app.processEvents()

        proc = processor.ProcessorMainFunction()  # instance of the ProcessorMainFunction class

        try:
            # Setup the inversion process
            proc.predict_main.prediction_setup(model_meta=self.model_meta_file, algorithm=self.algorithm, img_in=self.image,
                                               res_out=self.out_image, out_mode=self.out_mode,
                                               mask_ndvi=self.mask_ndvi, ndvi_thr=self.ndvi_thr,
                                               ndvi_bands=self.ndvi_bands, mask_image=self.mask_image,
                                               geo_in=self.geo_file, fixed_geos=self.geo_fixed,
                                               spatial_geo=self.spatial_geo, paras=self.paras)
        except ValueError as e:
            self.abort(message="Failed to setup inversion: {}".format(str(e)))
            return

        try:
            # call the prediction method
            proc.predict_main.predict_from_dump(prg_widget=self.prg_widget, qgis_app=self.main.qgis_app)
        except ValueError as e:
            if str(e) == "Inversion canceled":
                self.abort(message=str(e))
            else:
                self.abort(message="An error occurred during inversion: {}".format(str(e)))
            self.prg_widget.gui.lblCancel.setText("")
            self.prg_widget.gui.allow_cancel = True
            self.prg_widget.gui.close()
            return

        self.prg_widget.gui.lblCaption_r.setText('Prediction Finished! Writing Output...')
        self.main.qgis_app.processEvents()

        try:
            # Write the results to (a) file(s)
            proc.predict_main.write_prediction()
        except ValueError as e:
            self.abort(message="An error occurred while trying to write output-image: {}".format(str(e)))
            return

        self.prg_widget.gui.lblCancel.setText("")
        self.prg_widget.gui.allow_cancel = True
        self.prg_widget.gui.close()
        QMessageBox.information(self.gui, "Finish", "ML mapping finished")
        self.gui.close()

    def open_train_gui(self):
        # Open the GUI for training new models
        from lmuvegetationapps.Processor.Processor_Training_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()
        self.gui.close()


# Popup-GUI to specify Nodat-values manually
class Nodat:
    def __init__(self, main):
        self.main = main
        self.gui = NodatGUI()
        self.connections()
        self.image = None

    def init(self, image_type, image):
        topstring = '%s @ %s' % (image_type, image)
        self.gui.lblSource.setText(topstring)
        self.gui.txtNodat.setText("")
        self.image = image
        self.nodat = None

    def connections(self):
        self.gui.cmdCancel.clicked.connect(lambda: self.gui.close())
        self.gui.cmdOK.clicked.connect(lambda: self.ok())

    def ok(self):
        if self.gui.txtNodat.text() == "":
            QMessageBox.critical(self.gui, "No Data", "A no data value must be supplied for this image!")
            return
        else:
            try:
                nodat = int(self.gui.txtNodat.text())
            except ValueError:
                QMessageBox.critical(self.gui, "No number", "'%s' is not a valid number" % self.gui.txtNodat.text())
                self.gui.txtNodat.setText("")
                return
        self.nodat = nodat
        #self.gui.close()


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
        self.ann_inversion = MLInversion(self)
        self.nodat_widget = Nodat(self)
        self.prg_widget = PRG(self)

    def show(self):
        self.ann_inversion.gui.show()


if __name__ == '__main__':
    from enmapbox.testing import start_app
    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())
