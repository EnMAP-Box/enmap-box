# -*- coding: utf-8 -*-
"""
***************************************************************************
    PWR_GUI.py - LMU Agri Apps - Plant Water Retrieval tool (PWR) - GUI
    -----------------------------------------------------------------------
    begin                : 10/2018
    copyright            : (C) 2018 Matthias Wocher
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
"""
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel
import sys
import os
from qgis.PyQt.QtWidgets import *
from PyQt5.QtGui import QPixmap
from _classic.hubflow.core import *
from lmuvegetationapps.PWR.PWR_core import PWR_core
from lmuvegetationapps import APP_DIR

pathUI_pwr = os.path.join(APP_DIR, 'Resources/UserInterfaces/PWR.ui')
pathUI_nodat = os.path.join(APP_DIR, 'Resources/UserInterfaces/Nodat.ui')
pathUI_prgbar = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')
pathIMG = os.path.join(APP_DIR, "Resources/PWR_showImg.PNG")

from enmapbox.gui.utils import loadUi

class PWR_GUI(QDialog):
    mLayer: QgsMapLayerComboBox
    def __init__(self, parent=None):
        super(PWR_GUI, self).__init__(parent)
        loadUi(pathUI_pwr, self)
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)

class Nodat_GUI(QDialog):
    def __init__(self, parent=None):
        super(Nodat_GUI, self).__init__(parent)
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

class PWR:

    def __init__(self, main):
        self.main = main
        self.gui = PWR_GUI()
        self.initial_values()
        self.connections()
        label = QLabel(self.gui.pwrImage)
        pixelmap = QPixmap(pathIMG)
        label.setPixmap(pixelmap)
        self.gui.pwrImage.resize(pixelmap.width(), pixelmap.height())
        self.gui.pwrImage.show()

    def initial_values(self):
        self.image = None
        self.nodat = [-999]*2
        self.division_factor = 1.0
        self.NDWI_th = -0.9
        self.out_path = None
        self.addItem = []
        self.gui.mLayer.setLayer(None)

    def connections(self):
        self.gui.cmdInputImage.clicked.connect(lambda: self.open_file(mode="imgSelect"))
        self.gui.mLayer.layerChanged.connect(lambda: self.open_file(mode="imgDropdown"))
        self.gui.cmdOutputImage.clicked.connect(lambda: self.open_file(mode="output"))

        self.gui.SpinNDWI.valueChanged.connect(lambda: self.NDWI_th_change())

        self.gui.pushRun.clicked.connect(lambda: self.run_pwr())
        self.gui.pushClose.clicked.connect(lambda: self.gui.close())

    def open_file(self, mode):
        if mode == "imgSelect":
            if self.image is not None:
                self.image = None
            bsq_input = QFileDialog.getOpenFileName(caption='Select Input Image')[0]
            if not bsq_input:
                return
            self.addItem.append(bsq_input)
            self.gui.mLayer.setAdditionalItems(self.addItem)
            self.gui.mLayer.setCurrentText(bsq_input)

            self.image = bsq_input
            self.image_read()

        elif mode == "imgDropdown":
            if self.image is not None:
                self.image = None
            if self.gui.mLayer.currentLayer() is not None:
                input = self.gui.mLayer.currentLayer()
                bsq_input = input.source()
            elif len(self.gui.mLayer.currentText()) > 0:
                bsq_input = self.gui.mLayer.currentText()
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

    def image_read(self):
        try:
            meta = self.get_image_meta(image=self.image, image_type="Input Image")
        except ValueError as e:
            self.abort(message=str(e))
            return
        if meta is None:
            self.dtype = None
            return
        else:
            self.dtype = meta[4]
        if self.dtype == 2 or self.dtype == 3 or self.dtype == 4 or self.dtype == 5:
            QMessageBox.information(self.gui, "Integer Input",
                                        "Integer input image:\nTool requires float [0.0-1.0]:\nDivision factor set to 10000")
            self.division_factor = 10000
            self.gui.spinDivisionFactor.setText(str(self.division_factor))
        if None in meta:
            self.image = None
            self.nodat[0] = None
            return
        else:
            self.gui.lblNodatImage.setText(str(meta[0]))
            self.gui.txtNodatOutput.setText(str(meta[0]))
            self.nodat[0] = meta[0]

    def get_image_meta(self, image, image_type):
        try:
            dataset: RasterDataset = openRasterDataset(image)
        except:
            QMessageBox.critical(self.gui, 'Input Image',
                                 'Image could not be read. Please make sure it is a valid ENVI image')
            return
        ds = dataset.gdalDataset()
        metadict = dataset.metadataDict()
        nrows = ds.RasterYSize
        ncols = ds.RasterXSize
        nbands = ds.RasterCount
        dtype = ds.GetRasterBand(1).DataType  # gdal.GDT_Int16
        if nbands < 2:
            raise ValueError("Input is not a multi-band image")
        try:
            nodata = int(metadict['ENVI']['data ignore value'])
            return nodata, nbands, nrows, ncols, dtype
        except:
            self.main.nodat_widget.init(image_type=image_type, image=image)
            self.main.nodat_widget.gui.setModal(True)  # parent window is blocked
            self.main.nodat_widget.gui.exec_()  # unlike .show(), .exec_() waits with execution of the code, until the app is closed
            return self.main.nodat_widget.nodat, nbands, nrows, ncols, dtype

    def NDWI_th_change(self):
        self.NDWI_th = self.gui.SpinNDWI.value()

    def run_pwr(self):
        if self.image is None:
            QMessageBox.critical(self.gui, "No image selected", "Please select an image to continue!")
            return
        elif self.out_path is None:
            QMessageBox.critical(self.gui, "No output file selected", "Please select an output file for your image!")
            return
        elif self.gui.txtNodatOutput.text()=="":
            QMessageBox.critical(self.gui, "No Data Value", "Please specify No Data Value!")
            return
        else:
            try:
                self.nodat[1] = int(self.gui.txtNodatOutput.text())
            except:
                QMessageBox.critical(self.gui, "Error", "'%s' is not a valid  No Data Value!" % self.gui.txtNodatOutput.text())
                return
        try:
            self.division_factor = float(self.gui.spinDivisionFactor.text())
        except:
            QMessageBox.critical(self.gui, "Error", "'%s' is not a valid division factor!" % self.gui.spinDivisionFactor.text())
            return


        # show progressbar - window
        self.main.prg_widget.gui.lblCaption_l.setText("Plant Water Retrieval")
        self.main.prg_widget.gui.lblCaption_r.setText("Reading Input Image...this may take several minutes")
        self.main.prg_widget.gui.prgBar.setValue(0)
        self.main.prg_widget.gui.setModal(True)
        self.main.prg_widget.gui.show()
        self.main.qgis_app.processEvents()

        try:
            iPWR = PWR_core(nodat_val=self.nodat, division_factor=self.division_factor)
            iPWR.initialize_PWR(input=self.image, output=self.out_path, lims=[930, 1060], NDVI_th=self.NDWI_th)
        except MemoryError:
            QMessageBox.critical(self.gui, 'error', "File too large to read. More RAM needed")
            self.main.prg_widget.gui.allow_cancel = True
            self.main.prg_widget.gui.close()
        except ValueError as e:
            QMessageBox.critical(self.gui, 'error', str(e))
            self.main.prg_widget.gui.allow_cancel = True  # The window may be cancelled
            self.main.prg_widget.gui.close()
            return

        try:  # give it a shot
            result = iPWR.execute_PWR(prg_widget=self.main.prg_widget, qgis_app=self.main.qgis_app)

        except:
            QMessageBox.critical(self.gui, 'error', "Calculation cancelled.")
            self.main.prg_widget.gui.allow_cancel = True
            self.main.prg_widget.gui.close()
            return

        self.main.prg_widget.gui.lblCaption_r.setText("Writing Output-File")
        self.main.qgis_app.processEvents()

        iPWR.write_image(result=result)
        # try:
        #
        # except:
        #     #QMessageBox.critical(self.gui, 'error', "An unspecific error occured while trying to write image data")
        #     self.main.prg_widget.gui.allow_cancel = True
        #     self.main.prg_widget.gui.close()
        #     return

        self.main.prg_widget.gui.allow_cancel = True
        self.main.prg_widget.gui.close()

        QMessageBox.information(self.gui, "Finish", "Calculation of PWR finished successfully")
        # self.gui.close()

    def abort(self, message):
        QMessageBox.critical(self.gui, "Error", message)

class Nodat:
    def __init__(self, main):
        self.main = main
        self.gui = Nodat_GUI()
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
        self.gui.cmdOK.clicked.connect(lambda: self.OK())

    def OK(self):
        if self.gui.txtNodat.text() == "":
            QMessageBox.critical(self.gui, "No Data", "A no data value must be supplied for this image!")
            return
        else:
            try:
                nodat = int(self.gui.txtNodat.text())
            except:
                QMessageBox.critical(self.gui, "No number", "'%s' is not a valid number" % self.gui.txtNodat.text())
                self.gui.txtNodat.setText("")
                return
        self.nodat = nodat
        self.gui.close()

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

class MainUiFunc:
    def __init__(self):
        self.qgis_app = QApplication.instance()
        self.pwr = PWR(self)
        self.nodat_widget = Nodat(self)
        self.prg_widget = PRG(self)

    def show(self):
        self.pwr.gui.show()

if __name__ == '__main__':
    from enmapbox.testing import start_app
    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())
