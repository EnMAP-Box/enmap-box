from typing import Optional

import numpy as np

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapboxprocessing.rasterreader import RasterReader
from hsvcolorrasterrendererapp.hsvcolorrasterrenderer import HsvColorRasterRenderer
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QCheckBox, QMainWindow, QComboBox, QLineEdit, QRadioButton
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer, QgsMapLayerProxyModel, QgsMapSettings
from qgis.gui import QgsMapCanvas, QgsRasterBandComboBox, QgsDoubleSpinBox, QgsMapLayerComboBox
from typeguard import typechecked


@typechecked
class HsvColorRasterRendererDialog(QMainWindow):
    mLayer: QgsMapLayerComboBox
    mBand1: QgsRasterBandComboBox
    mBand2: QgsRasterBandComboBox
    mBand3: QgsRasterBandComboBox
    mMin1: QLineEdit
    mMin2: QLineEdit
    mMin3: QLineEdit
    mMax1: QLineEdit
    mMax2: QLineEdit
    mMax3: QLineEdit
    mMinMaxUser: QRadioButton
    mMinMaxPercentile: QRadioButton
    mP1: QgsDoubleSpinBox
    mP2: QgsDoubleSpinBox
    mExtent: QComboBox
    mAccuracy: QComboBox

    mLiveUpdate: QCheckBox
    mApply: QToolButton

    EstimatedAccuracy, ActualAccuracy = 0, 1
    WholeRasterExtent, CurrentCanvasExtent = 0, 1

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mP1.setClearValue(self.mP1.value())
        self.mP2.setClearValue(self.mP2.value())

        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mBand1.bandChanged.connect(self.onLiveUpdate)
        self.mBand2.bandChanged.connect(self.onLiveUpdate)
        self.mBand3.bandChanged.connect(self.onLiveUpdate)

        self.mP1.valueChanged.connect(self.onLiveUpdate)
        self.mP2.valueChanged.connect(self.onLiveUpdate)
        self.mExtent.currentIndexChanged.connect(self.onLiveUpdate)
        self.mAccuracy.currentIndexChanged.connect(self.onLiveUpdate)

        self.mApply.clicked.connect(self.onApplyClicked)

    def currentLayer(self) -> Optional[QgsRasterLayer]:
        return self.mLayer.currentLayer()

    def currentExtent(self) -> Optional[SpatialExtent]:
        layer = self.currentLayer()
        if layer is None:
            return None

        if self.mExtent.currentIndex() == self.WholeRasterExtent:
            return SpatialExtent(layer.crs(), layer.extent())
        elif self.mExtent.currentIndex() == self.CurrentCanvasExtent:
            mapSettings: QgsMapSettings = self.mMapCanvas.mapSettings()
            return SpatialExtent(mapSettings.destinationCrs(), self.mMapCanvas.extent()).toCrs(layer.crs())
        else:
            raise ValueError()

    def currentSampleSize(self) -> int:
        if self.mAccuracy.currentIndex() == self.EstimatedAccuracy:
            return int(QgsRasterLayer.SAMPLE_SIZE)
        elif self.mAccuracy.currentIndex() == self.ActualAccuracy:
            return 0  # use all pixel
        else:
            raise ValueError()

    def currentRenderer(self) -> Optional[HsvColorRasterRenderer]:
        layer = self.currentLayer()
        if layer is None:
            return None

        band1 = self.mBand1.currentBand()
        band2 = self.mBand2.currentBand()
        band3 = self.mBand3.currentBand()

        if -1 in [band1, band2, band3]:
            return None

        quantile_range = self.mP1.value(), self.mP2.value()

        extent = self.currentExtent()
        extent = extent.intersect(layer.extent())
        sampleSize = self.currentSampleSize()

        reader = RasterReader(layer)
        bandList = [band1, band2, band3]
        width, height = reader.samplingWidthAndHeight(band1, extent, sampleSize)
        array = reader.array(bandList=bandList, width=width, height=height, boundingBox=extent)
        maskArray = np.all(reader.maskArray(array, bandList), axis=0)
        array1, array2, array3 = array
        values1 = array1[maskArray]
        values2 = array2[maskArray]
        values3 = array3[maskArray]

        if len(values1) == 0:
            return None

        if self.mMinMaxPercentile.isChecked():
            min1, max1 = np.percentile(values1, quantile_range)
            min2, max2 = np.percentile(values2, quantile_range)
            min3, max3 = np.percentile(values3, quantile_range)

            self.mMin1.setText(str(min1))
            self.mMin2.setText(str(min2))
            self.mMin3.setText(str(min3))
            self.mMax1.setText(str(max1))
            self.mMax2.setText(str(max2))
            self.mMax3.setText(str(max3))

        min1 = float(self.mMin1.text())
        min2 = float(self.mMin2.text())
        min3 = float(self.mMin3.text())
        max1 = float(self.mMax1.text())
        max2 = float(self.mMax2.text())
        max3 = float(self.mMax3.text())

        # make renderer
        renderer = HsvColorRasterRenderer()
        renderer.setRange(min1, min2, min3, max1, max2, max3)
        renderer.setBands(band1, band2, band3)

        return renderer

    def onLayerChanged(self):

        # get map canvas
        self.mMapCanvas = None
        layer = self.currentLayer()
        for mapDock in self.enmapBox.dockManager().mapDocks():
            if layer in mapDock.mapCanvas().layers():
                self.mMapCanvas = mapDock.mapCanvas()
                break

        # update gui
        self.mBand1.setLayer(layer)
        self.mBand2.setLayer(layer)
        self.mBand3.setLayer(layer)
        self.mBand1.setBand(-1)
        self.mBand2.setBand(-1)
        self.mBand3.setBand(-1)

        if layer is None:
            return

        renderer = layer.renderer()
        if isinstance(renderer, HsvColorRasterRenderer):
            self.mBand1.setBand(renderer.band1)
            self.mBand2.setBand(renderer.band2)
            self.mBand3.setBand(renderer.band3)
        else:
            self.mBand1.setBand(1)
            self.mBand2.setBand(min(2, layer.bandCount()))
            self.mBand3.setBand(min(3, layer.bandCount()))

    def onApplyClicked(self):
        layer = self.currentLayer()
        if layer is None:
            return
        renderer = self.currentRenderer()
        if renderer is None:
            return
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def onLiveUpdate(self):
        if self.mLiveUpdate.isChecked():
            self.onApplyClicked()
