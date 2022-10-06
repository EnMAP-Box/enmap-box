from os.path import join
from typing import Optional, Tuple

import numpy as np
from osgeo import gdal

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QCheckBox, QMainWindow, QComboBox, QLineEdit, QRadioButton
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMultiBandColorRenderer, QgsRasterLayer, QgsMapLayerProxyModel, QgsMapSettings
from qgis.gui import QgsMapCanvas, QgsRasterBandComboBox, QgsDoubleSpinBox, QgsMapLayerComboBox
from typeguard import typechecked


@typechecked
class MultiSourceMultiBandColorRendererDialog(QMainWindow):
    mLayerRgbName: QLineEdit
    mLayerRgb: QgsMapLayerComboBox
    mLayer1: QgsMapLayerComboBox
    mLayer2: QgsMapLayerComboBox
    mLayer3: QgsMapLayerComboBox
    mBand1: QgsRasterBandComboBox
    mBand2: QgsRasterBandComboBox
    mBand3: QgsRasterBandComboBox
    mLock2: QToolButton
    mLock3: QToolButton
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

        from enmapbox import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        for mLayer in [self.mLayer1, self.mLayer2, self.mLayer3]:
            mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
            mLayer.setExcludedProviders(['wms'])

        self.mP1.setClearValue(self.mP1.value())
        self.mP2.setClearValue(self.mP2.value())

        self.mLayer1.layerChanged.connect(self.onLayerChanged)
        self.mLayer2.layerChanged.connect(self.onLayerChanged)
        self.mLayer3.layerChanged.connect(self.onLayerChanged)

        self.mLayer1.layerChanged.connect(self.mBand1.setLayer)
        self.mLayer2.layerChanged.connect(self.mBand2.setLayer)
        self.mLayer3.layerChanged.connect(self.mBand3.setLayer)

        self.mBand1.bandChanged.connect(self.onBandChanged)
        self.mBand2.bandChanged.connect(self.onBandChanged)
        self.mBand3.bandChanged.connect(self.onBandChanged)

        self.mLock2.clicked.connect(self.onLockClicked)
        self.mLock3.clicked.connect(self.onLockClicked)

        self.mP1.valueChanged.connect(self.onLiveUpdate)
        self.mP2.valueChanged.connect(self.onLiveUpdate)
        self.mExtent.currentIndexChanged.connect(self.onLiveUpdate)
        self.mAccuracy.currentIndexChanged.connect(self.onLiveUpdate)

        self.mApply.clicked.connect(self.onApplyClicked)

    def findDisplayLayer(self) -> Optional[QgsRasterLayer]:
        name = self.mLayerRgbName.text()
        mapCanvas = self.enmapBox.currentMapCanvas()
        if mapCanvas is None:
            return None

        layer1, layer2, layer3 = self.currentLayers()
        if None in [layer1, layer2, layer3]:
            return None
        band1 = self.mBand1.currentBand()
        band2 = self.mBand2.currentBand()
        band3 = self.mBand3.currentBand()
        if -1 in [band1, band2, band3]:
            return None

        # find layer
        for layer in mapCanvas.layers():
            if isinstance(layer, QgsRasterLayer):
                if layer.name() == name:
                    return layer

        return None

    def makeDisplaySource(self) -> Optional[str]:
        name = self.mLayerRgbName.text()
        layer1, layer2, layer3 = self.currentLayers()
        if None in [layer1, layer2, layer3]:
            return None
        band1 = self.mBand1.currentBand()
        band2 = self.mBand2.currentBand()
        band3 = self.mBand3.currentBand()
        for band, layer in zip([band1, band2, band3], [layer1, layer2, layer3]):
            if band < 1 or band > layer.bandCount():
                return None

        # prepare source
        dsR = gdal.Translate(join('/vsimem/', name, 'red.vrt'), layer1.source(), bandList=[band1], format='VRT',
                             outputType=gdal.GDT_Float32)
        dsG = gdal.Translate(join('/vsimem/', name, 'green.vrt'), layer2.source(), bandList=[band2], format='VRT',
                             outputType=gdal.GDT_Float32)
        dsB = gdal.Translate(join('/vsimem/', name, 'blue.vrt'), layer3.source(), bandList=[band3], format='VRT',
                             outputType=gdal.GDT_Float32)
        uri = join('/vsimem/', name, 'rgb.vrt')
        ds = gdal.BuildVRT(uri, [dsR, dsG, dsB], separate=True)
        ds.GetRasterBand(1).SetDescription(RasterReader(layer1).bandName(band1) + ' [' + layer1.name() + ']')
        ds.GetRasterBand(2).SetDescription(RasterReader(layer2).bandName(band2) + ' [' + layer2.name() + ']')
        ds.GetRasterBand(3).SetDescription(RasterReader(layer3).bandName(band3) + ' [' + layer3.name() + ']')

        return uri

    def makeDisplayLayer(self) -> Optional[QgsRasterLayer]:
        source = self.makeDisplaySource()
        if source is None:
            return None

        layer = self.findDisplayLayer()
        if layer is None:
            layer = QgsRasterLayer(source, self.mLayerRgbName.text(), 'gdal')
            mapDock = self.enmapBox.currentMapDock()
            if mapDock is None:
                return
            mapDock.insertLayer(0, layer)
            self.mMapCanvas = self.enmapBox.currentMapCanvas()
        else:
            Utils.setLayerDataSource(layer, 'gdal', source, RasterReader(source).extent())
        self.mLayerRgb.setLayer(layer)
        return layer

    def currentLayers(self) -> Tuple[Optional[QgsRasterLayer], Optional[QgsRasterLayer], Optional[QgsRasterLayer]]:
        return self.mLayer1.currentLayer(), self.mLayer2.currentLayer(), self.mLayer3.currentLayer()

    def currentExtent(self) -> Optional[SpatialExtent]:
        layer = self.mLayerRgb.currentLayer()
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

    def currentRenderer(self) -> Optional[QgsMultiBandColorRenderer]:
        layer = self.mLayerRgb.currentLayer()
        if layer is None:
            return None

        quantile_range = self.mP1.value(), self.mP2.value()

        extent = self.currentExtent()
        extent = extent.intersect(layer.extent())
        sampleSize = self.currentSampleSize()
        reader = RasterReader(layer)
        width, height = reader.samplingWidthAndHeight(1, extent, sampleSize)
        array = reader.array(bandList=[1, 2, 3], width=width, height=height, boundingBox=extent)
        maskArray = np.all(reader.maskArray(array, [1, 2, 3]), axis=0)
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
        renderer = Utils.multiBandColorRenderer(
            layer.dataProvider(), [1, 2, 3], [min1, min2, min3], [max1, max2, max3]
        )
        return renderer

    def onLayerChanged(self):
        layer = self.makeDisplayLayer()
        if layer is None:
            return

        self.onLiveUpdate()

    def onBandChanged(self):
        if self.mLock2.isChecked():
            self.mBand2.setBand(self.mBand1.currentBand())
        if self.mLock3.isChecked():
            self.mBand3.setBand(self.mBand1.currentBand())

        self.onLayerChanged()

    def onLockClicked(self):
        if self.mLock2.isChecked():
            self.mBand2.setEnabled(False)
        else:
            self.mBand2.setEnabled(True)
        if self.mLock3.isChecked():
            self.mBand3.setEnabled(False)
        else:
            self.mBand3.setEnabled(True)
        self.onBandChanged()

    def onApplyClicked(self):
        layer = self.makeDisplayLayer()
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
