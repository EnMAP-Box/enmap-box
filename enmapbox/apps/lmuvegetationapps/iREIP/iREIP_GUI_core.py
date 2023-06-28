# -*- coding: utf-8 -*-
"""
***************************************************************************
    iREIP_GUI_core.py - LMU Agri Apps - interactive Red Edge Inflection Point Tool
    -----------------------------------------------------------------------
    begin                : 10/2019
    copyright            : (C) 2019 Matthias Wocher
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
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel


from _classic.hubflow.core import *
import numpy as np
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import Qt
from lmuvegetationapps import APP_DIR
import warnings

import sys
import os
from scipy.interpolate import *
from scipy.signal import savgol_filter
from enmapbox.qgispluginsupport.qps.pyqtgraph import pyqtgraph as pg
from enmapbox.gui.utils import loadUi

pathUI_ireip = os.path.join(APP_DIR, 'Resources/UserInterfaces/iREIP.ui')
pathUI_nodat = os.path.join(APP_DIR, 'Resources/UserInterfaces/Nodat.ui')
pathUI_prg = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')


class iREIP_GUI(QDialog):
    mLayer: QgsMapLayerComboBox

    def __init__(self, parent=None):
        super(iREIP_GUI, self).__init__(parent)
        loadUi(pathUI_ireip, self)
        QApplication.instance().installEventFilter(self)
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        # fix the sendHoverEvent crash by replacing the slot function
        self.rangeView.scene().sendHoverEvents = self.onHoverEvent
        self.firstDerivView.scene().sendHoverEvents = self.onHoverEvent
        self.secondDerivView.scene().sendHoverEvents = self.onHoverEvent


        self.plotItems = (self.rangeView.getPlotItem(), self.firstDerivView.getPlotItem(),
                          self.secondDerivView.getPlotItem())

        # add color settings to the viewbox context menu
        from qgis.gui import QgsColorButton
        self.btnBackgroundColor = QgsColorButton()

        self.btnBackgroundColor.colorChanged.connect(self.set_background_color)
        self.btnAxisColor = QgsColorButton()
        # self.btnAxisColor.colorChanged.connect([self.setAxisColor(canvas, QColor('white')) for canvas in self.plotItems])

        self.rangeView.setBackground(QColor('black'))
        self.firstDerivView.setBackground(QColor('black'))
        self.secondDerivView.setBackground(QColor('black'))

        # set default colors
        [self.set_axis_color(canvas, QColor('white')) for canvas in self.plotItems]
        self.set_background_color(QColor('black'))

    def set_axis_color(self, canvas, color: QColor):
        for name in canvas.axes.keys():
            ax = canvas.getAxis(name)
            if ax:
                ax.setPen(QColor(color))
                ax.setTextPen(QColor(color))

    def set_background_color(self, color: QColor):
        if not isinstance(color, QColor):
            color = QColor(color)
        assert isinstance(color, QColor)
        if color != self.btnBackgroundColor.color():
            self.btnBackgroundColor.setColor(color)
        else:
            # self.btnBackgroundColor.setColor(QColor(color))
            self.rangeView.setBackground(QColor(color))
            self.firstDerivView.setBackground(QColor(color))
            self.secondDerivView.setBackground(QColor(color))

    def onHoverEvent(self, *args, **kwds):
        """
        Does nothing. Just to avoid calling the PyQtGraph routine which can fail
        """
        pass


class Nodat_GUI(QDialog):
    def __init__(self, parent=None):
        super(Nodat_GUI, self).__init__(parent)
        loadUi(pathUI_nodat, self)


class PRG_GUI(QDialog):
    def __init__(self, parent=None):
        super(PRG_GUI, self).__init__(parent)
        loadUi(pathUI_prg, self)

        self.allow_cancel = False

    def closeEvent(self, event):
        if self.allow_cancel:
            event.accept()
        else:
            event.ignore()


class iREIP:
    def __init__(self, main):
        self.main = main
        self.gui = iREIP_GUI()
        self.initial_values()
        self.connections()
        self.init_plot()

    def initial_values(self):
        self.image = None
        self.out_path = None
        self.limits = [680, 770]
        self.useSavgolay = 0
        self.neighbors = 13
        self.plot_spec = None
        self.max_ndvi_pos = None
        self.ndvi_spec = None
        self.nodat = [-999] * 2
        self.division_factor = 1.0
        self.calc_deriv_flag = [False, False]  # First, Second Derivative [First, Second]
        self.addItem = []
        self.gui.mLayer.setLayer(None)

    def connections(self):

        self.gui.cmdInputImage.clicked.connect(lambda: self.open_file(mode="imgSelect"))
        self.gui.mLayer.layerChanged.connect(lambda: self.open_file(mode="imgDropdown"))
        self.gui.cmdOutputImage.clicked.connect(lambda: self.open_file(mode="output"))

        self.gui.lowWaveEdit.returnPressed.connect(
            lambda: self.limits_changed(self.gui.lowWaveEdit))
        self.gui.upWaveEdit.returnPressed.connect(
            lambda: self.limits_changed(self.gui.upWaveEdit))
        self.gui.neighborEdit.returnPressed.connect(lambda: self.neighbors_changed())

        self.gui.savGolayCheckBox.stateChanged.connect(lambda: self.sav_golay_changed())

        self.gui.spinDivisionFactor.returnPressed.connect(lambda: self.division_factor_changed())
        self.gui.cmdFindNDVI.clicked.connect(lambda: self.init_ireip(mode='init'))

        self.gui.checkFirstDeriv.stateChanged.connect(lambda: self.calc_deriv())
        self.gui.checkSecondDeriv.stateChanged.connect(lambda: self.calc_deriv())

        self.gui.pushFullRange.clicked.connect(lambda: self.plot_change(mode="full"))
        self.gui.pushSetRange.clicked.connect(lambda: self.plot_change(mode="zoom"))

        self.gui.pushRun.clicked.connect(lambda: self.init_ireip(mode='run'))
        self.gui.pushClose.clicked.connect(lambda: self.gui.close())

    def open_file(self, mode):
        if mode == "imgSelect":
            if self.image is not None:
                self.reset()
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
                self.reset()
            if self.gui.mLayer.currentLayer() is not None:
                input = self.gui.mLayer.currentLayer()
                bsq_input = input.source()
            elif len(self.gui.mLayer.currentText()) > 0:
                bsq_input = self.gui.mLayer.currentText()
            else:
                self.reset()
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
        dtype = ds.GetRasterBand(1).DataType  # i.e. gdal.GDT_Int16
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

    def reset(self):
        self.max_ndvi_pos = None
        self.init_plot()
        self.image = None



    def limits_changed(self, textfeld):
        if self.image is None:
            QMessageBox.warning(self.gui, "No image loaded",
                                "Please load an image, press 'Find' and adjust boundaries")
        else:
            if textfeld == self.gui.lowWaveEdit:
                try:
                    self.limits[0] = int(str(textfeld.text()))
                except ValueError:
                    QMessageBox.critical(self.gui, "Not a number",
                                         "'%s' is not a valid number" % textfeld.text())
                    textfeld.setText(str(self.limits[0]))
            elif textfeld == self.gui.upWaveEdit:
                try:
                    self.limits[1] = int(str(textfeld.text()))
                except ValueError:
                    QMessageBox.critical(self.gui, "Not a number",
                                         "'%s' is not a valid number" % textfeld.text())
                    textfeld.setText(str(self.limits[1]))
                self.limits[1] = int(str(textfeld.text()))
            if not self.limits[1] > self.limits[0]:
                ValueError(QMessageBox.critical(self.gui, "Error",
                                                "Lower boundary not smaller than upper"))
                self.gui.lowWaveEdit.setText(str(self.limits[0]))
                self.gui.upWaveEdit.setText(str(self.limits[0] + 1))
                self.limits[1] = int(str(self.gui.upWaveEdit.text()))
                self.limits[0] = int(str(self.gui.lowWaveEdit.text()))

            if self.max_ndvi_pos == None:
                self.init_plot()
            else:
                self.plot_example(self.max_ndvi_pos)

    def neighbors_changed(self):
        if self.image is None:
            QMessageBox.warning(self.gui, "No image loaded",
                                "Please load an image, press 'Find' and adjust boundaries")
        else:
            try:
                self.neighbors = int(str(self.gui.neighborEdit.text()))
            except ValueError:
                QMessageBox.critical(self.gui, "Not a number",
                                     "'%s' is not a valid number" % self.gui.neighborEdit.text())
                self.gui.neighborEdit.setText(str(self.neighbors))
            if (self.neighbors % 2) == 0:
                QMessageBox.warning(self.gui, "Savitzky-Golay Error", "Neighbor value must be odd")
                self.neighbors += 1
                self.gui.neighborEdit.setText(str(self.neighbors))
            if not self.neighbors > 2:
                QMessageBox.warning(self.gui, "Savitzky-Golay Error", "Window length must be > 2")
                self.neighbors = 3
                self.gui.neighborEdit.setText(str(self.neighbors))
            self.init_ireip(mode='init')
            self.plot_example(self.max_ndvi_pos)

    def sav_golay_changed(self):
        if self.gui.savGolayCheckBox.isChecked():
            self.gui.neighborEdit.setEnabled(True)
            self.useSavgolay = 1
            if self.image is None:
                pass
            elif self.image is not None:
                self.init_ireip(mode='init')
                self.plot_example(self.max_ndvi_pos)
        else:
            self.gui.neighborEdit.setEnabled(False)
            self.useSavgolay = 0
            if self.image is None:
                pass
            elif self.image is not None:
                self.init_ireip(mode='init')
                self.plot_example(self.max_ndvi_pos)

    def division_factor_changed(self):
        if self.image is None:
            QMessageBox.warning(self.gui, "No image loaded",
                                "Please load an image, press 'Find' and adjust boundaries")
        else:
            try:
                self.division_factor = int(str(self.gui.spinDivisionFactor.text()))
                self.gui.spinDivisionFactor.setText(str(self.division_factor))
            except ValueError:
                QMessageBox.critical(self.gui, "Not a number",
                                     "'%s' is not a valid number" % self.gui.neighborEdit.text())
        self.init_ireip(mode='init')
        self.plot_example(self.max_ndvi_pos)

    def calc_deriv(self):
        if self.gui.checkFirstDeriv.isChecked():
            self.calc_deriv_flag[0] = True
        else:
            self.calc_deriv_flag[0] = False
        if self.gui.checkSecondDeriv.isChecked():
            self.calc_deriv_flag[1] = True
        else:
            self.calc_deriv_flag[1] = False

    def init_plot(self):
        labelStyle = {'color': '#FFF', 'font-size': '12px'}

        self.gui.lblPixelLocation.setText("")
        self.gui.ipLabel.setText("")
        self.gui.ipPosLabel.setText("")

        self.gui.rangeView.plot(clear=True)
        self.gui.rangeView.setLabel(axis='left', text="Reflectance [%]", **labelStyle)
        self.gui.rangeView.setLabel('bottom', text="Wavelength [nm]", **labelStyle)

        self.gui.rangeView.addItem(pg.InfiniteLine(self.limits[0], pen="w"))
        self.gui.rangeView.addItem(pg.InfiniteLine(self.limits[1], pen="w"))
        self.gui.rangeView.setXRange(350, 2500, padding=0)

        self.gui.firstDerivView.plot(clear=True)
        self.gui.firstDerivView.setLabel('left', text="[-]", **labelStyle)
        self.gui.firstDerivView.setLabel('bottom', text="Wavelength [nm]", **labelStyle)
        self.gui.firstDerivView.addItem(pg.InfiniteLine(self.limits[0], pen="w"))
        self.gui.firstDerivView.addItem(pg.InfiniteLine(self.limits[1], pen="w"))
        self.gui.firstDerivView.setXRange(350, 2500, padding=0)

        self.gui.secondDerivView.plot(clear=True)
        self.gui.secondDerivView.setLabel('left', text="[-]", **labelStyle)
        self.gui.secondDerivView.setLabel('bottom', text="Wavelength [nm]", **labelStyle)
        self.gui.secondDerivView.addItem(pg.InfiniteLine(self.limits[0], pen="w"))
        self.gui.secondDerivView.addItem(pg.InfiniteLine(self.limits[1], pen="w"))
        self.gui.secondDerivView.setXRange(350, 2500, padding=0)

    def plot_example(self, max_ndvi_pos):
        self.gui.lblPixelLocation.setText("Image pixel: row: %s | col: %s" % (
            str(max_ndvi_pos[1]), str(max_ndvi_pos[2])))
        self.gui.lblPixelLocation.setStyleSheet('color: green')
        self.plot_spec = self.core.interp_watervapor_1d(self.core.ndvi_spec / self.division_factor)

        self.smooth_array, self.first_deriv, self.second_deriv, self.reip = self.core.derivate_1d(
            in_array=self.plot_spec, prg_widget=self.main.prg_widget, qgis_app=self.main.qgis_app)

        self.gui.rangeView.plot(self.core.wl, self.smooth_array, clear=True, pen="g", fillLevel=0,
                                fillBrush=(255, 255, 255, 30),
                                name='maxNDVIspec')
        self.gui.rangeView.addItem(pg.InfiniteLine(self.limits[0], pen="w"))
        self.gui.rangeView.addItem(pg.InfiniteLine(self.limits[1], pen="w"))

        self.gui.firstDerivView.plot(self.core.wl, self.first_deriv, clear=True, pen="g", fillLevel=0,
                                     fillBrush=(255, 255, 255, 30),
                                     name='first_deriv')
        self.gui.firstDerivView.addItem(pg.InfiniteLine(self.limits[0], pen="w"))
        self.gui.firstDerivView.addItem(pg.InfiniteLine(self.limits[1], pen="w"))

        self.gui.secondDerivView.plot(self.core.wl, self.second_deriv, clear=True, pen="g", fillLevel=0,
                                      fillBrush=(255, 255, 255, 30),
                                      name='second_deriv')
        self.gui.secondDerivView.addItem(pg.InfiniteLine(self.limits[0], pen="w"))
        self.gui.secondDerivView.addItem(pg.InfiniteLine(self.limits[1], pen="w"))

        self.gui.rangeView.setYRange(0, np.max(self.smooth_array))
        self.gui.firstDerivView.setYRange(np.min(self.first_deriv), np.max(self.first_deriv))
        self.gui.secondDerivView.setYRange(np.min(self.second_deriv), np.max(self.second_deriv))

        if self.reip is not None:
            self.gui.secondDerivView.addItem(
                pg.InfiniteLine(self.reip,
                                pen=pg.mkPen(color=(255, 255, 255), style=Qt.DashLine)))

            self.gui.ipLabel.setText("Inflection point found at")
            self.gui.ipLabel.setStyleSheet('color: green')
            self.gui.ipPosLabel.setText("{:6.2f}".format(self.reip) + " nm")
            self.gui.ipPosLabel.setStyleSheet('color: green')
        else:
            self.gui.ipLabel.setText("No unique inflection point found")
            self.gui.ipLabel.setStyleSheet('color: red')
            self.gui.ipPosLabel.setText("")

    def plot_change(self, mode):
        if self.plot_spec is not None:
            self.gui.rangeView.setYRange(0, np.max(self.smooth_array))
            self.gui.firstDerivView.setYRange(np.min(self.first_deriv), np.max(self.first_deriv))
            self.gui.secondDerivView.setYRange(np.min(self.second_deriv), np.max(self.second_deriv))
        if mode == 'zoom':
            low, high = self.limits
            self.gui.rangeView.setXRange(low, high)
            self.gui.firstDerivView.setXRange(low, high)
            self.gui.secondDerivView.setXRange(low, high)
        if mode == 'full':
            low, high = [350, 2500]
            self.gui.rangeView.setXRange(low, high)
            self.gui.firstDerivView.setXRange(low, high)
            self.gui.secondDerivView.setXRange(low, high)

    def init_ireip(self, mode):
        if mode == 'init':
            if self.image is None:
                QMessageBox.critical(self.gui, "No image selected",
                                     "Please select an image to continue!")
                return
            try:
                self.division_factor = float(self.gui.spinDivisionFactor.text())
            except:
                QMessageBox.critical(self.gui, "Error", "'%s' is not a valid division factor!" % self.gui.spinDivisionFactor.text())
                return

            if not self.max_ndvi_pos:
                # show progressbar - window
                self.main.prg_widget.gui.lblCaption_l.setText("Searching NDVI > 0.85")
                self.main.prg_widget.gui.lblCaption_r.setText(
                    "Reading Input Image...this may take some time")
                self.main.prg_widget.gui.prgBar.setValue(0)
                self.main.prg_widget.gui.setModal(True)
                self.main.prg_widget.gui.show()
                self.main.qgis_app.processEvents()

            #   try:
                self.core = iREIP_core(nodat_val=self.nodat, division_factor=self.division_factor,
                                       max_ndvi_pos=self.max_ndvi_pos, ndvi_spec=self.ndvi_spec)

                self.core.initialize_iREIP(input=self.image, output=None,
                                           limits=self.limits,
                                           deriv=self.calc_deriv_flag, useSavgolay=self.useSavgolay,
                                           neighbors=self.neighbors, mode='find')
                self.core.in_raster = self.core.read_image(image=self.image)

            #   except MemoryError:
            #   QMessageBox.critical(self.gui, 'error', "File too large to read. More RAM needed")
            #    self.main.prg_widget.gui.allow_cancel = True
            #    self.main.prg_widget.gui.close()
            #   except ValueError as e:
            #    QMessageBox.critical(self.gui, 'error', str(e))

                self.max_ndvi_pos, self.ndvi_spec = self.core.findHighestNDVIindex(
                    in_raster=self.core.in_raster,
                    prg_widget=self.main.prg_widget, qgis_app=self.main.qgis_app)

                self.main.prg_widget.gui.allow_cancel = True  # The window may be cancelled
                self.main.prg_widget.gui.close()
                self.plot_example(self.max_ndvi_pos)
            else:

                self.core = iREIP_core(nodat_val=self.nodat, division_factor=self.division_factor,
                                     max_ndvi_pos=self.max_ndvi_pos, ndvi_spec=self.ndvi_spec)
                self.core.initialize_iREIP(input=self.image, output=None,
                                           limits=self.limits, deriv=self.calc_deriv_flag,
                                           useSavgolay=self.useSavgolay, neighbors=self.neighbors,
                                           mode='find')



        if mode == 'run':
            if self.image is None:
                QMessageBox.critical(self.gui, "No image loaded",
                                     "Please load an image to continue!")
                return
            if str(self.gui.txtOutputImage.text()) == "":
                QMessageBox.warning(self.gui, "No output file selected",
                                    "Please select an output file for your image!")
                return
            else:
                self.out_path = str(self.gui.txtOutputImage.text())

            # show progressbar - window
            self.main.prg_widget.gui.lblCancel.setText("")
            self.main.prg_widget.gui.lblCaption_l.setText("Searching Inflection Point")
            self.main.prg_widget.gui.lblCaption_r.setText(
                "Reading Input Image...this may take several minutes")
            self.main.prg_widget.gui.prgBar.setValue(0)
            self.main.prg_widget.gui.setModal(True)
            self.main.prg_widget.gui.show()
            self.main.qgis_app.processEvents()

            try:
                self.iiREIP = iREIP_core(nodat_val=self.nodat, division_factor=self.division_factor,
                                         max_ndvi_pos=self.max_ndvi_pos, ndvi_spec=self.ndvi_spec)
                self.iiREIP.initialize_iREIP(input=self.image, output=self.out_path,
                                             limits=self.limits,
                                             deriv=self.calc_deriv_flag, useSavgolay=self.useSavgolay,
                                             neighbors=self.neighbors, mode='run')

            except MemoryError:
                QMessageBox.critical(self.gui, 'error', "File too large to read")
                self.main.prg_widget.gui.allow_cancel = True
                self.main.prg_widget.gui.close()
            except ValueError as e:
                QMessageBox.critical(self.gui, 'error', str(e))
                self.main.prg_widget.gui.allow_cancel = True  # The window may be cancelled
                self.main.prg_widget.gui.close()
                return

            if self.gui.txtNodatOutput.text() == "":
                QMessageBox.warning(self.gui, "No Data Value", "Please specify No Data Value!")
                # QMessageBox.critical(self.gui, "No Data Value", "Please specify No Data Value!")
                return
            else:
                try:
                    self.nodat[1] = int(self.gui.txtNodatOutput.text())
                except:
                    QMessageBox.critical(self.gui, "Error",
                                         "'%s' is not a valid  No Data Value!" % self.gui.txtNodatOutput.text())
                    return
            try:
                self.division_factor = float(self.gui.spinDivisionFactor.text())
            except:
                QMessageBox.critical(self.gui, "Error",
                                     "'%s' is not a valid division factor!" % self.gui.spinDivisionFactor.text())
                return

            try:
                self.iiREIP.in_raster = self.core.in_raster[self.core.valid_bands, :, :]
                del self.core.in_raster
                if self.division_factor != 1.0:
                    self.iiREIP.in_raster = np.divide(self.iiREIP.in_raster, self.division_factor)
            except:
                self.iiREIP.in_raster = self.iiREIP.read_image(image=self.image)
                if self.division_factor != 1.0:
                    self.iiREIP.in_raster = np.divide(self.iiREIP.in_raster, self.division_factor)

            # try:  # give it a shot
            result, first_deriv, second_deriv = self.iiREIP.execute_iREIP(
                in_raster=self.iiREIP.in_raster,
                prg_widget=self.main.prg_widget, qgis_app=self.main.qgis_app)
            # except:
            # QMessageBox.critical(self.gui, 'error', "Calculation cancelled.")
            # self.main.prg_widget.gui.allow_cancel = True
            # self.main.prg_widget.gui.close()
            # return

            self.main.prg_widget.gui.lblCaption_r.setText("Writing REIP Output-File")
            self.main.qgis_app.processEvents()

            self.iiREIP.write_ireip_image(result=result)

            if first_deriv is not None:
                self.main.prg_widget.gui.lblCaption_r.setText("Writing 1st Derivative Output-File")
                self.main.qgis_app.processEvents()

                self.iiREIP.write_deriv_image(deriv=first_deriv, mode="first")

            if second_deriv is not None:
                self.main.prg_widget.gui.lblCaption_r.setText("Writing 2nd Derivative Output-File")
                self.main.qgis_app.processEvents()

                self.iiREIP.write_deriv_image(deriv=second_deriv, mode="second")

            # try:
            #
            # except:
            #     #QMessageBox.critical(self.gui, 'error', "An unspecific error occured while trying to write image data")
            #     self.main.prg_widget.gui.allow_cancel = True
            #     self.main.prg_widget.gui.close()
            #     return

            self.main.prg_widget.gui.allow_cancel = True
            self.main.prg_widget.gui.close()

            QMessageBox.information(self.gui, "Finish", "Calculation finished successfully")
            #self.gui.close()

    def abort(self, message):
        QMessageBox.critical(self.gui, "Error", message)

class iREIP_core:

    def __init__(self, nodat_val, division_factor, max_ndvi_pos, ndvi_spec):
        self.nodat = nodat_val
        self.division_factor = division_factor
        self.max_ndvi_pos = max_ndvi_pos
        self.ndvi_spec = ndvi_spec
        self.initial_values()

    def initial_values(self):
        self.wavelengths = None
        self.limits = None
        self.delta = 0
        self.pixel_total = None
        self.grid, self.nrows, self.ncols, self.nbands = (
        None, None, None, None)
        self.default_exclude = [i for j in
                                (range(983, 1129), range(1430, 1650), range(2050, 2151))
                                for i in j]
        self.enmap_exclude = range(78, 88)

    def initialize_iREIP(self, input, output, limits, deriv, useSavgolay, neighbors, mode):
        self.grid, self.wl, self.nbands, self.nrows, self.ncols, self.dtype = self.read_image_meta(image=input)
        self.n_wl = len(self.wl)
        self.pixel_total = self.nrows * self.ncols
        self.useSavgolay = useSavgolay
        self.neighbors = neighbors
        self.calc_deriv_flag = deriv
        if mode == 'find':
            self.output = None
        elif mode == 'run':
            self.output = output

        self.limits = (self.find_closest(lambd=limits[0]), self.find_closest(lambd=limits[1]))
        self.low_limit, self.upp_limit = (self.limits[0], self.limits[1])

        if len(self.wl) == 242:  # temporary solution for overlapping EnMap-Testdata Bands
            self.wl = np.delete(self.wl, self.enmap_exclude)  # temporary solution!
            self.n_wl = len(self.wl)
            self.nbands = len(self.wl)

        self.valid_wl = [self.wl[i] for i in range(self.n_wl) if
                         self.wl[i] >= self.low_limit and self.wl[i] <= self.upp_limit]
        self.valid_wl = [int(round(i, 0)) for i in self.valid_wl]

        self.valid_bands = [i for i, x in enumerate(self.wl) if x in list(self.valid_wl)]


    def read_image(self, image):
        dataset = openRasterDataset(image)
        raster = dataset.readAsArray()
        if len(self.wl) > 2000:
            try:
                raster[self.default_exclude, :, :] = 0
            except:
                pass
        if len(raster) == 242:  # temporary solution for overlapping EnMap-Testdata Bands
            raster = np.delete(raster, self.enmap_exclude, axis=0)  # temporary solution!
        return raster

    def read_image_window(self, image):
        dataset = openRasterDataset(image)
        raster = dataset.readAsArray()
        if len(self.wl) > 2000:
            try:
                raster[self.default_exclude, :, :] = 0
            except:
                pass
        if len(raster) == 242:  # temporary solution for overlapping EnMap-Testdata Bands
            raster = np.delete(raster, self.enmap_exclude, axis=0)  # temporary solution!
        window = raster[self.valid_bands, :, :]
        return window

    @staticmethod
    def read_image_meta(image):
        dataset: RasterDataset = openRasterDataset(image)
        ds = dataset.gdalDataset()
        if dataset.grid() is not None:
            grid = dataset.grid()
        else:
            raise Warning('No coordinate system information provided in ENVI header file')
        metadict = dataset.metadataDict()
        nrows = ds.RasterYSize
        ncols = ds.RasterXSize
        nbands = ds.RasterCount
        dtype = ds.GetRasterBand(1).DataType  # gdal.GDT_Int16

        try:
            wave_dict = metadict['ENVI']['wavelength']
        except:
            raise ValueError('No wavelength units provided in ENVI header file')

        if metadict['ENVI']['wavelength'] is None:
            raise ValueError('No wavelength units provided in ENVI header file')
        elif metadict['ENVI']['wavelength units'].lower() in \
                ['nanometers', 'nm', 'nanometer']:
            wave_convert = 1
        elif metadict['ENVI']['wavelength units'].lower() in \
                ['micrometers', 'µm', 'micrometer']:
            wave_convert = 1000
        else:
            raise ValueError(
                "Wavelength units must be nanometers or micrometers. Got '%s' instead" %
                metadict['ENVI'][
                    'wavelength units'])

        wl = [float(item) * wave_convert for item in wave_dict]
        wl = [int(i) for i in wl]

        return grid, wl, nbands, nrows, ncols, dtype

    def write_ireip_image(self, result):
        output = Raster.fromArray(array=result, filename=self.output, grid=self.grid)

        output.dataset().setMetadataItem('data ignore value', self.nodat[1], 'ENVI')

        for band in output.dataset().bands():
            band.setDescription(
                'Inflection point between %i and %i nm' % (self.limits[0], self.limits[1]))
            band.setNoDataValue(self.nodat[1])

    def write_deriv_image(self, deriv, mode):  #

        if mode == "first":
            band_string_nr = ['band ' + str(x+1) for x, i in enumerate(self.valid_bands)]
            deriv_output = self.output.split(".")

            for row in range(deriv.shape[1]):
                for col in range(deriv.shape[2]):
                    if np.mean(deriv[:, row, col]) == 0:
                        deriv[:, row, col] = self.nodat[1]
                    else: continue

            deriv_output = deriv_output[0] + "_1st_deriv" + "." + deriv_output[1]
            output = Raster.fromArray(array=deriv, filename=deriv_output, grid=self.grid)

            output.dataset().setMetadataItem('data ignore value', self.nodat[1], 'ENVI')

            for i, band in enumerate(output.dataset().bands()):
                band.setDescription(band_string_nr[i])
                band.setNoDataValue(self.nodat[1])

            output.dataset().setMetadataItem(key='wavelength', value=self.valid_wl,
                                             domain='ENVI')
            output.dataset().setMetadataItem(key='wavelength units', value='Nanometers', domain='ENVI')

        if mode == "second":
            band_string_nr = ['band ' + str(x+1) for x, i in enumerate(self.valid_bands)]
            deriv_output = self.output.split(".")
            deriv_output = deriv_output[0] + "_2nd_deriv" + "." + deriv_output[1]

            for row in range(deriv.shape[1]):
                for col in range(deriv.shape[2]):
                    if np.mean(deriv[:, row, col]) == 0:
                        deriv[:, row, col] = self.nodat[1]
                    else: continue
                    
            output = Raster.fromArray(array=deriv, filename=deriv_output, grid=self.grid)

            output.dataset().setMetadataItem('data ignore value', self.nodat[1], 'ENVI')

            for i, band in enumerate(output.dataset().bands()):
                band.setDescription(band_string_nr[i])
                band.setNoDataValue(self.nodat[1])

            output.dataset().setMetadataItem(key='wavelength', value=self.valid_wl, domain='ENVI')
            output.dataset().setMetadataItem(key='wavelength units', value='Nanometers', domain='ENVI')

    def find_closest(self, lambd):
        distances = [abs(lambd - self.wl[i]) for i in range(self.n_wl)]
        return self.wl[distances.index(min(distances))]

    def interp_watervapor_1d(self, in_array):
        x = np.arange(len(in_array))
        self.res = np.empty(shape=np.shape(in_array))

        if np.nan not in in_array:
            idx = np.asarray(np.nonzero(in_array))
            idx = idx.flatten()

            interp = interp1d(x[idx], in_array[idx], axis=0, fill_value='extrapolate')
            self.res = interp(x)
        else:
            self.res = in_array
        self.res[self.res < 0] = 0
        return self.res

    def interp_watervapor_3d(self, in_matrix):
        x = np.arange(len(in_matrix))
        try:
            in_matrix[self.default_exclude] = 0
        except: pass
        self.res3d = np.empty(shape=np.shape(in_matrix))
        for row in range(in_matrix.shape[1]):
            for col in range(in_matrix.shape[2]):
                if np.mean(in_matrix[:, row, col]) != self.nodat[0]:
                    idx = np.asarray(np.nonzero(in_matrix[:, row, col]))
                    idx = idx.flatten()
                    interp = interp1d(x[idx], in_matrix[idx, row, col], axis=0, fill_value='extrapolate')
                    self.res3d[:, row, col] = interp(x)
                else:
                    self.res3d[:, row, col] = in_matrix[:, row, col]
        return self.res3d

    def derivate_1d(self, in_array, prg_widget=None, qgis_app=None):  # derivative for plot canvases

        self.prg = prg_widget
        self.qgis_app = qgis_app

        if self.useSavgolay == 1:
            smooth_array = savgol_filter(in_array[:], window_length=self.neighbors, polyorder=2)
        else:
            smooth_array = in_array[:]
        first_deriv = np.gradient(smooth_array)
        second_deriv = np.gradient(first_deriv)
        window = second_deriv[self.valid_bands]
        try:
            reip_index_1 = int(np.where(np.signbit(window[:-1]) != np.signbit(window[1:]))[0])
            reip_index_2 = int(np.where(np.signbit(window[:-1]) != np.signbit(window[1:]))[0]) + 1
            val_1 = (window[reip_index_1])
            val_2 = (window[reip_index_2])
            reip_pos_1 = int(self.valid_wl[reip_index_1])
            reip_pos_2 = int(self.valid_wl[reip_index_2])
            steps = (reip_pos_2 - reip_pos_1)**2 + 100
            pos_wl, tracker = list(zip(*(list(zip(*(
                np.linspace(reip_pos_1, reip_pos_2, steps), np.linspace(val_1, val_2, steps)))))))
            reip_pos_index = (np.abs(list(tracker))).argmin()
            reip_pos = pos_wl[reip_pos_index]

        except:
            QMessageBox.information(self.prg.gui, "Warning",
                                    "Inflection Point is not unique.\nUse Savitzky-Golay filter or decrease the range width.")
            reip_pos = None

        return smooth_array, first_deriv, second_deriv, reip_pos

    def derivate_3d(self, in_matrix):  # derivatives for output

        self.prg.gui.lblCaption_l.setText(
            "Calculating spectra derivatives...")

        reip_pos = np.empty(shape=(1, np.shape(in_matrix)[1], np.shape(in_matrix)[2]))

        if self.useSavgolay == 1:
            try:
                smooth_matrix = savgol_filter(in_matrix,
                                              window_length=self.neighbors, polyorder=2, axis=0)
            except:
                QMessageBox.information(self.prg.gui, "Warning",
                                 "Savitzky-Golay-Filter Error. Neighbors have been set -2.")
                try:
                    smooth_matrix = savgol_filter(in_matrix,
                                                  window_length=self.neighbors-2, polyorder=2, axis=0)
                except:
                    try:
                        QMessageBox.information(self.prg.gui, "Warning",
                                                "Savitzky-Golay-Filter Error. Last try: Neighbors have been set -2 once more.")
                        smooth_matrix = savgol_filter(in_matrix,
                                                      window_length=self.neighbors-2, polyorder=2, axis=0)
                    except: ValueError("Savitzky-Golay-Filter could not be applied. Try to uncheck filtering.")

        else:
            smooth_matrix = in_matrix # no Filter applied.

        smooth_matrix = smooth_matrix[self.valid_bands]
        d1 = np.gradient(smooth_matrix, axis=0)
        d2 = np.gradient(d1, axis=0)


        for row in range(in_matrix.shape[1]):
            for col in range(in_matrix.shape[2]):
                if np.mean(in_matrix[:, row, col]) != self.nodat[0]:
                    #  check for sign change within set range of 2. derivative
                    reip_index_1 = np.where(np.signbit(d2[:-1, row, col]) != np.signbit(d2[1:, row, col]))[0]
                    reip_index_2 = \
                        np.where(np.signbit(d2[:-1, row, col]) != np.signbit(d2[1:, row, col]))[0] + 1
                    if len(reip_index_1) > 1 or len(reip_index_2) > 1:
                        reip_index_1 = int(np.min(reip_index_1))
                        reip_index_2 = int(np.min(reip_index_2))
                        # reip_pos[:, row, col] = self.nodat[1]
                    else:
                        try:
                            reip_index_1 = int(reip_index_1)
                            reip_index_2 = int(reip_index_2)
                        except:
                            reip_pos[:, row, col] = self.nodat[1]
                            continue

                    #  resolve accuracy of IP-position
                    val_1 = d2[reip_index_1, row, col]
                    val_2 = d2[reip_index_2, row, col]
                    if val_2 > val_1:
                        reip_pos[:, row, col] = self.nodat[1]
                        continue
                    reip_pos_1 = self.valid_wl[reip_index_1]
                    reip_pos_2 = self.valid_wl[reip_index_2]
                    steps = (reip_pos_2 - reip_pos_1) ** 2 + 100
                    pos_wl, tracker = list(zip(*(list(zip(*(
                        np.linspace(reip_pos_1, reip_pos_2, steps),
                        np.linspace(val_1, val_2, steps)))))))
                    reip_pos_index = (np.abs(list(tracker))).argmin()
                    reip_pos[:, row, col] = pos_wl[reip_pos_index]
                else:
                    reip_pos[:, row, col] = self.nodat[1]

                self.prgbar_process(pixel_no=row * self.ncols + col)

        if self.calc_deriv_flag[0] is False and self.calc_deriv_flag[1] is False:
            return reip_pos, None, None
        elif self.calc_deriv_flag[0] is True and self.calc_deriv_flag[1] is False:
            return reip_pos, d1, None
        elif self.calc_deriv_flag[0] is False and self.calc_deriv_flag[1] is True:
            return reip_pos, None, d2
        else:
            return reip_pos, d1, d2

    def execute_iREIP(self, in_raster, prg_widget=None, qgis_app=None):
        self.prg = prg_widget
        self.qgis_app = qgis_app
        res, first_deriv, second_deriv = self.derivate_3d(in_raster)

        return res, first_deriv, second_deriv

    def findHighestNDVIindex(self, in_raster, prg_widget=None, qgis_app=None):  # acc. to hNDVI Oppelt(2002)

        self.prg = prg_widget
        self.qgis_app = qgis_app

        NDVI_closest = [self.find_closest_wl(lambd=827), self.find_closest_wl(lambd=668)]
        self.NDVI_bands = [i for i, x in enumerate(self.wl) if x in NDVI_closest]
        in_raster = in_raster / self.division_factor

        for row in range(np.shape(in_raster)[1]):
            for col in range(np.shape(in_raster)[2]):
                if np.mean(in_raster[:, row, col]) != self.nodat[0]:
                    R827 = in_raster[self.NDVI_bands[1], row, col]
                    R668 = in_raster[self.NDVI_bands[0], row, col]
                    if R827 or R668 > 0.0:
                        if R827 > 0.4:
                            try:
                                NDVI = float(R827 - R668) / float(R827 + R668)
                                if NDVI > 0.85:
                                    self.NDVI = NDVI
                                    self.row = row
                                    self.col = col
                                    self.ndvi_spec = in_raster[:, row, col]
                                    break
                            except ZeroDivisionError:
                                continue
                                # NDVI = 0
                        else:
                            continue
                    else:
                        continue
                    self.prgbar_process(pixel_no=row * self.ncols + col)
                else:
                    continue
            else:
                continue
            break
        if self.NDVI:
            self.max_index = [self.NDVI, self.row, self.col]  # raster pos where NDVI > 0.85 was found
            return self.max_index, self.ndvi_spec
        else:
            self.max_index = [0, 0, 0]
            self.ndvi_spec = np.empty(np.shape(in_raster)[0])
            self.ndvi_spec[:] = np.nan
            QMessageBox.information(self.prg.gui, "Error", "No NDVI > 0.85 found, Check Data Input.")
            return self.max_index, self.ndvi_spec

    def find_closest_wl(self, lambd):
        distances = [abs(lambd - self.wl[i]) for i in range(self.n_wl)]
        return self.wl[distances.index(min(distances))]

    def find_closest_value(self, lambd, array):
        distances = [abs(lambd - array[i]) for i in range(len(array))]
        return array[distances.index(min(distances))]

    def prgbar_process(self, pixel_no):
        if self.prg:
            if self.prg.gui.lblCancel.text() == "-1":  # Cancel has been hit shortly before
                self.prg.gui.lblCancel.setText("")
                self.prg.gui.cmdCancel.setDisabled(False)
                raise ValueError("Calculation canceled")
            self.prg.gui.prgBar.setValue(
                pixel_no * 100 // self.pixel_total)  # progress value is index-orientated
            #self.prg.gui.lblCaption_l.setText("Processing...")
            if pixel_no % 100 == 0:
                self.prg.gui.lblCaption_r.setText("pixel %i of %i" % (pixel_no, self.pixel_total))
            self.qgis_app.processEvents()


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
            QMessageBox.critical(self.gui, "No Data",
                                 "A no data value must be supplied for this image!")
            return
        else:
            try:
                nodat = int(float(self.gui.txtNodat.text()))
            except:
                QMessageBox.critical(self.gui, "No number",
                                     "'%s' is not a valid number" % self.gui.txtNodat.text())
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
        self.ireip = iREIP(self)
        self.ireip_core = iREIP_core(nodat_val=None, division_factor=None, max_ndvi_pos=None,
                                     ndvi_spec=None)
        self.nodat_widget = Nodat(self)
        self.prg_widget = PRG(self)

    def show(self):
        self.ireip.gui.show()


if __name__ == '__main__':
    from enmapbox.testing import start_app
    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())

