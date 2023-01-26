from random import randint
from typing import Optional

from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QCheckBox, QMainWindow, QSpinBox, QGridLayout
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer, QgsMultiBandColorRenderer, QgsContrastEnhancement, QgsRasterMinMaxOrigin, \
    QgsMapLayerProxyModel
from qgis.gui import QgsMapCanvas, QgsRasterBandComboBox, QgsMapLayerComboBox
from typeguard import typechecked


@typechecked
class ColorSpaceExplorerDialog(QMainWindow):
    mLayer: QgsMapLayerComboBox
    mRedBand: QgsRasterBandComboBox
    mGreenBand: QgsRasterBandComboBox
    mBlueBand: QgsRasterBandComboBox
    mRandomBands: QToolButton
    mRedDelta: QSpinBox
    mGreenDelta: QSpinBox
    mBlueDelta: QSpinBox
    mRandomDelta: QToolButton
    mRandomDeltaMax: QSpinBox

    mPrevious: QToolButton
    mNext: QToolButton
    mPlay: QToolButton
    mFps: QSpinBox

    mGridLayout: QGridLayout

    mLiveUpdate: QCheckBox

    mOk: QToolButton
    mCancel: QToolButton
    mApply: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)

        self.mLayer.layerChanged.connect(self.onLayerChanged)

        for i in range(1, 17):
            mRgb: QToolButton = getattr(self, f'mRgb_{i}')
            text = mRgb.text()
            tmp = text.split(' ')
            bands = tmp[-1][1:-1].split('-')
            wavelengths = [str(CreateSpectralIndicesAlgorithm.WavebandMapping[
                                   CreateSpectralIndicesAlgorithm.translateSentinel2Band(band)
                               ][0]) + 'nm'
                           for band in bands]
            name = ' '.join(tmp[:-1])
            name += '\n(' + '-'.join(wavelengths) + ')'
            mRgb.setText(name)
            mRgb.bands = bands
            mRgb.clicked.connect(self.onPredefinedRgbClicked)

        self.mRedBand.bandChanged.connect(self.onLiveUpdate)
        self.mGreenBand.bandChanged.connect(self.onLiveUpdate)
        self.mBlueBand.bandChanged.connect(self.onLiveUpdate)

        self.mRandomBands.clicked.connect(self.onRandomBandsClicked)
        self.mNext.clicked.connect(self.onNextClicked)
        self.mPrevious.clicked.connect(self.onPreviousClicked)
        self.mPlay.clicked.connect(self.onPlayClicked)

        self.mRandomBands.clicked.connect(self.onRandomBandsClicked)
        self.mRandomDelta.clicked.connect(self.onRandomDeltaClicked)

        self.mApply.clicked.connect(self.onApplyClicked)
        self.onRandomDeltaClicked()

    def currentLayer(self) -> Optional[QgsRasterLayer]:
        return self.mLayer.currentLayer()

    def onLayerChanged(self):

        # stop animation
        self.mPlay.setChecked(False)

        # disconnect old map canvas
        if self.mMapCanvas is not None:
            try:
                self.mMapCanvas.extentsChanged.disconnect(self.onMapCanvasExtentsChanged)
            except Exception:
                pass

        # connect new map canvas
        self.mMapCanvas = None
        layer = self.currentLayer()

        for mapDock in self.enmapBox.dockManager().mapDocks():
            if layer in mapDock.mapCanvas().layers():
                self.mMapCanvas = mapDock.mapCanvas()
                break
        if self.mMapCanvas is not None:
            self.mMapCanvas.extentsChanged.connect(self.onMapCanvasExtentsChanged)

        # update gui
        if layer is not None and isinstance(layer.renderer(), QgsMultiBandColorRenderer):
            bandNoRed = layer.renderer().redBand()
            bandNoGreen = layer.renderer().greenBand()
            bandNoBlue = layer.renderer().blueBand()
        else:
            bandNoRed = bandNoGreen = bandNoBlue = 1

        self.mRedBand.setLayer(layer)
        self.mGreenBand.setLayer(layer)
        self.mBlueBand.setLayer(layer)

        self.mRedBand.setBand(bandNoRed)
        self.mGreenBand.setBand(bandNoGreen)
        self.mBlueBand.setBand(bandNoBlue)

        if layer is not None:
            bandCount = layer.bandCount()
        else:
            bandCount = 0

        for mDelta in [self.mRedDelta, self.mGreenDelta, self.mBlueDelta]:
            mDelta.setMinimum(-bandCount)
            mDelta.setMaximum(bandCount)
        self.mRandomDeltaMax.setMaximum(bandCount)

    def onMapCanvasExtentsChanged(self):
        pass

    def onPredefinedRgbClicked(self):
        layer = self.currentLayer()
        if layer is None:
            return

        mRgb = self.sender()
        bands = [CreateSpectralIndicesAlgorithm.translateSentinel2Band(band) for band in mRgb.bands]
        r, g, b = [CreateSpectralIndicesAlgorithm.findBroadBand(layer, band) for band in bands]
        self.mRedBand.setBand(r)
        self.mGreenBand.setBand(g)
        self.mBlueBand.setBand(b)

    def onRandomBandsClicked(self):
        layer = self.currentLayer()
        if layer is None:
            return

        self.mRedBand.setBand(randint(1, layer.bandCount()))
        self.mGreenBand.setBand(randint(1, layer.bandCount()))
        self.mBlueBand.setBand(randint(1, layer.bandCount()))

    def onRandomDeltaClicked(self):
        layer = self.currentLayer()
        if layer is None:
            return

        v = min(self.mRandomDeltaMax.value(), layer.bandCount())
        for mDelta in [self.mRedDelta, self.mGreenDelta, self.mBlueDelta]:
            mDelta.setValue(randint(-v, v))

    def nextBandNo(self, bandNo: int, delta: int, backwards) -> int:
        layer = self.currentLayer()
        if layer is None:
            return -1

        if backwards:
            delta = -delta
        bandNo += delta
        bandNo = ((bandNo - 1) % layer.bandCount()) + 1
        return bandNo

    def onNextClicked(self, *args, backwards=False):
        self.mRedBand.setBand(self.nextBandNo(self.mRedBand.currentBand(), self.mRedDelta.value(), backwards))
        self.mGreenBand.setBand(self.nextBandNo(self.mGreenBand.currentBand(), self.mGreenDelta.value(), backwards))
        self.mBlueBand.setBand(self.nextBandNo(self.mBlueBand.currentBand(), self.mBlueDelta.value(), backwards))

    def onPreviousClicked(self):
        self.onNextClicked(backwards=True)

    def onPlayClicked(self):
        self.onNextClicked()
        if self.mMapCanvas is not None:
            self.mMapCanvas.waitWhileRendering()
            if self.mPlay.isChecked():
                animationFrameLength = int(1000 / self.mFps.value())
                QTimer.singleShot(animationFrameLength, self.onPlayClicked)

    def onApplyClicked(self):

        if self.isHidden():
            self.mLayer.setLayer(None)
            return

        layer = self.currentLayer()
        if layer is None:
            return

        renderer = layer.renderer()
        if not isinstance(renderer, QgsMultiBandColorRenderer):
            renderer = QgsMultiBandColorRenderer(layer.dataProvider(), 1, 1, 1)
            layer.setRenderer(renderer)

        assert isinstance(renderer, QgsMultiBandColorRenderer)
        layer.renderer().setRedBand(self.mRedBand.currentBand())
        layer.renderer().setGreenBand(self.mGreenBand.currentBand())
        layer.renderer().setBlueBand(self.mBlueBand.currentBand())
        if hasattr(layer, 'setCacheImage'):
            layer.setCacheImage(None)

        algorithm = QgsContrastEnhancement.StretchToMinimumMaximum
        limits = QgsRasterMinMaxOrigin.CumulativeCut
        layer.setContrastEnhancement(algorithm, limits)  # rest is defined by the layer style

    def onLiveUpdate(self):
        if self.mLiveUpdate.isChecked():
            self.onApplyClicked()
