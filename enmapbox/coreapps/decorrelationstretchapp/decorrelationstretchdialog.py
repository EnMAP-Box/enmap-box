from math import sqrt
from typing import Optional

import numpy as np
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QCheckBox, \
    QMainWindow, QComboBox
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer, QgsMultiBandColorRenderer, QgsMapLayerProxyModel, QgsMapSettings
from qgis.gui import QgsMapCanvas, QgsRasterBandComboBox, QgsDoubleSpinBox, QgsMapLayerComboBox

from decorrelationstretchapp.decorrelationstretchrenderer import DecorrelationStretchRenderer
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapboxprocessing.rasterreader import RasterReader
from typeguard import typechecked


@typechecked
class DecorrelationStretchDialog(QMainWindow):
    mLayer: QgsMapLayerComboBox
    mRed: QgsRasterBandComboBox
    mGreen: QgsRasterBandComboBox
    mBlue: QgsRasterBandComboBox

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
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mP1.setClearValue(self.mP1.value())
        self.mP2.setClearValue(self.mP2.value())

        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mRed.bandChanged.connect(self.onLiveUpdate)
        self.mGreen.bandChanged.connect(self.onLiveUpdate)
        self.mBlue.bandChanged.connect(self.onLiveUpdate)
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

    def currentRenderer(self) -> Optional[DecorrelationStretchRenderer]:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import RobustScaler, MinMaxScaler

        layer = self.currentLayer()
        if layer is None:
            return None

        bandList = [band.currentBand() for band in [self.mRed, self.mGreen, self.mBlue]]
        if -1 in bandList:
            return None

        quantile_range = self.mP1.value(), self.mP2.value()

        extent = self.currentExtent()
        extent = extent.intersect(layer.extent())
        sampleSize = self.currentSampleSize()

        if sampleSize == 0:
            width = height = None  # derived by reader
        else:
            maxSize = int(sqrt(sampleSize))
            width = min(maxSize, layer.width())
            height = min(maxSize, layer.height())

        # read trainings data
        reader = RasterReader(layer)
        array = reader.array(bandList=bandList, width=width, height=height, boundingBox=extent)
        maskArray = np.all(reader.maskArray(array, bandList), axis=0)

        # fit transformers
        X = np.transpose([a[maskArray] for a in array])
        if len(X) == 0:
            return None

        pca = PCA(n_components=3)
        pca.fit(X)
        XPca = pca.transform(X)
        scaler1 = RobustScaler(with_centering=False, quantile_range=quantile_range)
        scaler1.fit(XPca)
        XPcaStretched = scaler1.transform(XPca)
        Xt = pca.inverse_transform(XPcaStretched)
        percentiles = np.percentile(Xt, quantile_range, axis=0)
        scaler2 = MinMaxScaler(feature_range=[0, 255], clip=True)
        scaler2.fit(percentiles)

        # make renderer
        renderer = DecorrelationStretchRenderer()
        renderer.setTransformer(pca, scaler1, scaler2)
        renderer.setBandList(bandList)

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
        self.mRed.setLayer(layer)
        self.mGreen.setLayer(layer)
        self.mBlue.setLayer(layer)
        self.mRed.setBand(-1)
        self.mGreen.setBand(-1)
        self.mBlue.setBand(-1)

        if layer is None:
            return

        renderer = layer.renderer()
        if isinstance(renderer, DecorrelationStretchRenderer):
            self.mRed.setBand(renderer.bandList[0])
            self.mGreen.setBand(renderer.bandList[1])
            self.mBlue.setBand(renderer.bandList[2])
        elif isinstance(renderer, QgsMultiBandColorRenderer):
            self.mRed.setBand(renderer.redBand())
            self.mGreen.setBand(renderer.greenBand())
            self.mBlue.setBand(renderer.blueBand())
        else:
            self.mRed.setBand(1)
            self.mGreen.setBand(min(2, layer.bandCount()))
            self.mBlue.setBand(min(3, layer.bandCount()))

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
