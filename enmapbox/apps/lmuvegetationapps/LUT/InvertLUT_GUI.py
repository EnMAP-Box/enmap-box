# -*- coding: utf-8 -*-
"""
***************************************************************************
    InverLUT_GUI.py - LMU Agri Apps - Inversion of pre-created PROSAIL/PROINFORM look-up-tables
    -----------------------------------------------------------------------
    begin                : 06/2018
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
    along with this software. If not, see <http://www.gnu.org/licenses/>.
***************************************************************************
"""
from qgis._gui import QgsMapLayerComboBox
from qgis._core import QgsMapLayerProxyModel

import sys
import os
# ensure to call QGIS before PyQtGraph
from qgis.PyQt.QtWidgets import *
from osgeo import gdal
import lmuvegetationapps.LUT.InvertLUT_core as Inverse
from lmuvegetationapps import APP_DIR
from enmapbox.gui.utils import loadUi
import numpy as np

pathUI_inversion = os.path.join(APP_DIR, 'Resources/UserInterfaces/InvertLUT.ui')
pathUI_wavelengths = os.path.join(APP_DIR, 'Resources/UserInterfaces/Select_Wavelengths.ui')
pathUI_nodat = os.path.join(APP_DIR, 'Resources/UserInterfaces/Nodat.ui')
pathUI_prgbar = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')


class GlobalInversionGUI(QDialog):
    mLayerImage: QgsMapLayerComboBox
    mLayerGeometry: QgsMapLayerComboBox
    mLayerMask: QgsMapLayerComboBox
    def __init__(self, parent=None):
        super(GlobalInversionGUI, self).__init__(parent)
        loadUi(pathUI_inversion, self)
        self.mLayerImage.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mLayerGeometry.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mLayerMask.setFilters(QgsMapLayerProxyModel.RasterLayer)

class SelectWavelengthsGUI(QDialog):

    def __init__(self, parent=None):
        super(SelectWavelengthsGUI, self).__init__(parent)
        loadUi(pathUI_wavelengths, self)


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
        # window may only be closed, if self.allow_cancel is TRUE (=Cancel Button hit)
        if self.allow_cancel:
            event.accept()
        else:
            event.ignore()


# class GlobalInversion manages the GUI for the inversion tool ###
class GlobalInversion:

    def __init__(self, main):
        self.main = main
        self.gui = GlobalInversionGUI()
        self.initial_values()
        self.connections()

    def initial_values(self):
        # exclude_wavelengths: from ... to [nm]; these are default values for atmospheric water vapor absorption
        self.exclude_wavelengths = [[1359, 1480], [1721, 2001]]
        self.ctype = 1
        self.nbfits = 0
        self.nbfits_type = "rel"
        self.noisetype = 0
        self.noiselevel = 0
        self.nodat = [-999] * 3
        self.exclude_bands, self.exclude_bands_model = (None, None)
        self.wl_compare = None
        self.n_wl = None
        self.image = None
        self.mask_image = None
        self.out_path = None
        self.out_mode = "single"

        self.geo_mode = "file"
        self.spatial_geo = False
        self.geo_file = None
        self.geo_fixed = [None] * 3

        self.conversion_factor = None

        self.lut_path = None
        self.wl = None
        self.addItemImage, self.addItemGeometry, self.addItemMask = ([], [], [])
        self.gui.mLayerImage.setLayer(None)
        self.gui.mLayerGeometry.setLayer(None)
        self.gui.mLayerMask.setLayer(None)

    def connections(self):
        # Input Images
        self.gui.mLayerImage.layerChanged.connect(lambda: self.open_file(mode="imgDropdown"))
        self.gui.cmdInputImage.clicked.connect(lambda: self.open_file(mode="imgSelect"))
        self.gui.cmdInputLUT.clicked.connect(lambda: self.open_file(mode="lut"))
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
        self.gui.chkMeanCalc.clicked.connect(lambda: self.geo_mean_calc())

        # Artificial Noise
        self.gui.radNoiseOff.clicked.connect(lambda: self.select_noise(mode=0))
        self.gui.radNoiseAdd.clicked.connect(lambda: self.select_noise(mode=1))
        self.gui.radNoiseMulti.clicked.connect(lambda: self.select_noise(mode=2))
        self.gui.radNoiseInvMulti.clicked.connect(lambda: self.select_noise(mode=3))

        # Cost Function
        self.gui.radRMSE.clicked.connect(lambda: self.select_costfun(mode=1))
        self.gui.radMAE.clicked.connect(lambda: self.select_costfun(mode=2))
        self.gui.radmNSE.clicked.connect(lambda: self.select_costfun(mode=3))
        self.gui.radRel.clicked.connect(lambda: self.select_costfun(cfun_type="rel"))
        self.gui.radAbs.clicked.connect(lambda: self.select_costfun(cfun_type="abs"))

        # Execute
        self.gui.cmdExcludeBands.clicked.connect(lambda: self.open_wavelength_selection())
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
            self.image_read()

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
            self.image_read()

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

    def image_read(self):
        try:
            meta = self.get_image_meta(image=self.image, image_type="Input Image")  # get metadata of image
            self.nodat[0], self.nbands, self.nrows, self.ncols, self.wl, self.wunit = meta
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
            self.exclude_bands = [i for i in range(len(self.wl)) if self.wl[i] < 400 or self.wl[i] > 2500
                                  or self.exclude_wavelengths[0][0] <= self.wl[i] <= self.exclude_wavelengths[0][1]
                                  or self.exclude_wavelengths[1][0] <= self.wl[i] <= self.exclude_wavelengths[1][1]]
            self.gui.txtExclude.setText(" ".join(str(i) for i in self.exclude_bands))  # join to string for lineEdit
            self.gui.txtExclude.setCursorPosition(0)

    def select_outputmode(self, mode):
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

    def geo_mean_calc(self):
        # defines whether geometry is spatially explicit or should be averaged over the whole image
        if self.gui.chkMeanCalc.isChecked():
            self.spatial_geo = False
        else:
            self.spatial_geo = True

    def select_noise(self, mode):
        # Enables and disables lineEdit for noise level
        if mode == 0:
            self.gui.txtNoiseLevel.setDisabled(True)
        else:
            self.gui.txtNoiseLevel.setDisabled(False)
        self.noisetype = mode

    def select_costfun(self, mode=None, cfun_type=None):
        if mode is not None:
            self.ctype = mode
        if cfun_type is not None:
            # switch between relative and absolute number of best fits
            if cfun_type == "rel":
                self.gui.txtAbs.setDisabled(True)
                self.gui.txtRel.setDisabled(False)
            elif cfun_type == "abs":
                self.gui.txtAbs.setDisabled(False)
                self.gui.txtRel.setDisabled(True)
            self.nbfits_type = cfun_type

    def abort(self, message):
        # pops up message boxes
        QMessageBox.critical(self.gui, "Error", message)

    def check_and_assign(self):
        # Image In
        if self.image is None:
            raise ValueError('Input Image missing')
        elif not os.path.isfile(self.image):
            raise ValueError('Input Image does not exist')

        # LUT
        if self.lut_path is None:
            raise ValueError('LUT metafile missing')
        elif not os.path.isfile(self.lut_path):
            raise ValueError('LUT metafile does not exist')

        # Output path
        self.out_path = self.gui.txtOutputImage.text().replace("\\", "/")
        if self.out_path is None:
            raise ValueError('Output file missing')
        else:
            # if user typed a file extension for the binary raster file, nothing happens; otherwise .bsq is added
            try:
                os.path.splitext(self.out_path)[1]
            except IndexError:
                self.out_path += ".bsq"

        # Geometry file:
        if self.geo_mode == "file":
            if self.geo_file is None:
                raise ValueError('Geometry-Input via file selected, but no file specified')
            elif not os.path.isfile(self.geo_file):
                raise ValueError('Geometry-Input file does not exist')

        elif self.geo_mode == "fix":
            self.gui.chkMeanCalc.setDisabled(True)
            if self.gui.txtSZA.text() == "" or self.gui.txtOZA.text() == "" or self.gui.txtRAA.text() == "":
                raise ValueError('Geometry-Input via fixed values selected, but angles are incomplete')
            else:
                try:
                    self.geo_fixed = [float(self.gui.txtSZA.text()),
                                      float(self.gui.txtOZA.text()),
                                      float(self.gui.txtRAA.text())]
                except ValueError:
                    raise ValueError('Cannot interpret Geometry angles as numbers')

        elif self.geo_mode == "off":
            self.geo_fixed = None
            self.geo_file = None

        # Noise
        if not self.noisetype == 0:
            if self.gui.txtNoiseLevel.text() == "":
                raise ValueError('Please specify level for artificial noise')

            else:
                self.noiselevel = self.gui.txtNoiseLevel.text()
                try:
                    self.noiselevel = float(self.noiselevel)
                except ValueError:
                    raise ValueError('Cannot interpret noise level as decimal number')

        # Cost Function Type:
        if self.nbfits_type == "rel":
            if self.gui.txtRel.text() == "":
                raise ValueError('Please specify number of best fits')
            else:
                self.nbfits = self.gui.txtRel.text()
                try:
                    self.nbfits = float(self.nbfits)
                except ValueError:
                    raise ValueError('Cannot interpret number of best fits as a real number')

        elif self.nbfits_type == "abs":
            if self.gui.txtAbs.text() == "":
                raise ValueError('Please specify number of best fits')
            else:
                self.nbfits = self.gui.txtAbs.text()
                try:
                    self.nbfits = int(self.nbfits)
                except ValueError:
                    raise ValueError('Cannot interpret number of best fits as a real number')

        # Mask
        if self.mask_image is not None:
            if not os.path.isfile(self.mask_image):
                raise ValueError('Mask Image does not exist')

        if self.gui.txtNodatOutput.text() == "":
            raise ValueError('Please specify no data value for output')
        else:
            try:
                self.nodat[2] = int(self.gui.txtNodatOutput.text())
            except ValueError:
                raise ValueError('%s is not a valid no data value for output' % self.gui.txtNodatOutput.text())

    def get_image_meta(self, image, image_type):
        # extracts meta information from the spectral image
        dataset = gdal.Open(image)
        if dataset is None:
            raise ValueError('{} could not be read. Please make sure it is a valid ENVI image'.format(image_type))
        else:
            nbands = dataset.RasterCount
            nrows = dataset.RasterYSize
            ncols = dataset.RasterXSize
            if image_type == "Mask Image":
                return nbands, nrows, ncols
            try:  # try and get no data value and convert it to integer
                nodata = int("".join(dataset.GetMetadataItem('data_ignore_value', 'ENVI').split()))
            # no dat not found or cannot be interpreted as intereg! No worries, the user can add it manually!
            except (AttributeError, ValueError):
                self.main.nodat_widget.init(image_type=image_type, image=image)
                self.main.nodat_widget.gui.setModal(True)  # parent window is blocked
                # unlike .show(), .exec_() waits with execution of the code, until the app is closed
                self.main.nodat_widget.gui.exec_()
                nodata = self.main.nodat_widget.nodat

            if image_type == "Geometry Image":
                return nodata, nbands, nrows, ncols

            elif image_type == "Input Image":
                try:  # extract wavelength information and convert to float
                    wavelengths = "".join(dataset.GetMetadataItem('wavelength', 'ENVI').split())
                    wavelengths = wavelengths.replace("{", "")
                    wavelengths = wavelengths.replace("}", "")
                    wavelengths = wavelengths.split(",")
                    wavelengths = [float(item) for item in wavelengths]
                except AttributeError:  # wavelength is not found as item in the header
                    raise ValueError('{}: file is missing wavelengths in header'.format(image))
                except ValueError:  # conversion to float fails
                    raise ValueError("{}: file's wavelengths cannot be be read".format(image))

                try:  # extract wavelength unit as item in the header
                    wl_units = "".join(dataset.GetMetadataItem('wavelength_units', 'ENVI').split())
                    if wl_units.lower() in ['nanometers', 'nm', 'nanometer']:  # any of these is accepted
                        wave_convert = 1  # factor is 1, as the methond expects nm anyway
                        wl_unit_str = 'nm'
                    elif wl_units.lower() in ['micrometers', 'µm', 'micrometer']:
                        wave_convert = 1000  # factor is 1000 to obtain nm
                        wl_unit_str = 'µm'
                    else:
                        raise ValueError('{}: Unknown wavelength unit {}'.format(image, wl_units))
                except AttributeError:
                    raise ValueError('{}: file is missing wavelength units in Header'.format(image))

                wavelengths = [item * wave_convert for item in wavelengths]  # obtain nm in any regard

                return nodata, nbands, nrows, ncols, wavelengths, wl_unit_str  # needs to be unpacked this way

    def run_inversion(self):
        try:
            self.check_and_assign()
        except ValueError as e:
            self.abort(message=str(e))
            return

        # Progress Bar
        self.prg_widget = self.main.prg_widget
        self.prg_widget.gui.lblCaption_l.setText("Global Inversion")
        self.prg_widget.gui.lblCaption_r.setText("Setting up inversion...")
        self.main.prg_widget.gui.prgBar.setValue(0)
        self.main.prg_widget.gui.setModal(True)
        self.prg_widget.gui.show()

        self.main.qgis_app.processEvents()

        inv = Inverse.RTMInversion()  # Create an instance of the Inversion class

        try:
            inv.inversion_setup(image=self.image, image_out=self.out_path, LUT_path=self.lut_path, ctype=self.ctype,
                                nbfits=self.nbfits, nbfits_type=self.nbfits_type, noisetype=self.noisetype,
                                noiselevel=self.noiselevel, wl_image=self.wl, exclude_bands=self.exclude_bands,
                                geo_image=self.geo_file, geo_fixed=self.geo_fixed, spatial_geo=self.spatial_geo,
                                mask_image=self.mask_image, out_mode=self.out_mode, nodat=self.nodat)
        except ValueError as e:  # to separate between errors in the inversion setup and actual performance
            self.abort(message="Failed to setup inversion: %s" % str(e))
            return

        try:
            inv.run_inversion(prg_widget=self.prg_widget, qgis_app=self.main.qgis_app)
        except ValueError as e:
            if str(e) == "Inversion canceled":  # the cancel button will return this string on purpose
                self.abort(message=str(e))
            else:
                self.abort(message="An error occurred during inversion: %s" % str(e))
            self.prg_widget.gui.lblCancel.setText("")
            self.prg_widget.gui.allow_cancel = True
            self.prg_widget.gui.close()
            return

        self.prg_widget.gui.lblCaption_r.setText("Writing Output-File...")
        self.main.qgis_app.processEvents()

        try:
            inv.write_image()
        except ValueError as e:
            self.abort(message="An error occurred while trying to write output-image: %s" % str(e))
            return

        self.prg_widget.gui.lblCancel.setText("")
        self.prg_widget.gui.allow_cancel = True
        self.prg_widget.gui.close()
        QMessageBox.information(self.gui, "Finish", "Inversion finished")
        self.gui.close()

    def open_wavelength_selection(self):
        try:
            self.invoke_selection()
        except ValueError as e:
            self.abort(message=str(e))

    def invoke_selection(self):
        # Check ImageIn
        if self.image is None:
            raise ValueError('Specify Input Image first')
        elif not os.path.isfile(self.image):
            raise ValueError('Input Image not found')

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
        if self.main.global_inversion.nbands < 10:
            width = 1
        elif self.main.global_inversion.nbands < 100:
            width = 2
        elif self.main.global_inversion.nbands < 1000:
            width = 3
        else:
            width = 4

        # Any bands with central wavelengths in the specified domain are excluded by default,
        # i.e. the GUI is prepared to add these to the exclude list;
        for i in range(self.main.global_inversion.nbands):
            if i in default_exclude:
                str_band_no = '{num:0{width}}'.format(num=i + 1, width=width)
                label = "band %s: %6.2f %s" % (str_band_no, self.main.global_inversion.wl[i],
                                               self.main.global_inversion.wunit)
                self.gui.lstExcluded.addItem(label)
            else:
                str_band_no = '{num:0{width}}'.format(num=i+1, width=width)
                label = "band %s: %6.2f %s" % (str_band_no, self.main.global_inversion.wl[i],
                                               self.main.global_inversion.wunit)
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
        self.main.global_inversion.exclude_bands = [int(raw_list[i].split(" ")[1][:-1]) - 1
                                                    for i in range(len(raw_list))]
        # Join the list to a string and set it to the txtExclude lineEdit
        exclude_string = " ".join(str(x + 1) for x in self.main.global_inversion.exclude_bands)
        self.main.global_inversion.gui.txtExclude.setText(exclude_string)

        # clean up
        for list_object in [self.gui.lstIncluded, self.gui.lstExcluded]:
            list_object.clear()

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
        self.global_inversion = GlobalInversion(self)
        self.select_wavelengths = SelectWavelengths(self)
        self.nodat_widget = Nodat(self)
        self.prg_widget = PRG(self)

    def show(self):
        self.global_inversion.gui.show()


if __name__ == '__main__':
    from enmapbox.testing import start_app
    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())
