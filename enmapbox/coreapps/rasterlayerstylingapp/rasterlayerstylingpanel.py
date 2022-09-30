from math import nan
from typing import Optional

from osgeo import gdal

from enmapbox import EnMAPBox
from enmapbox.gui.dataviews.dockmanager import DockPanelUI
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapbox.utils import BlockSignals
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDoubleSpinBox, QComboBox, QCheckBox, QToolButton, QLabel, QTabWidget, \
    QLineEdit, QTableWidget
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer, QgsSingleBandGrayRenderer, QgsRectangle, \
    QgsContrastEnhancement, QgsRasterRenderer, QgsMultiBandColorRenderer, QgsSingleBandPseudoColorRenderer, \
    QgsMapLayerProxyModel, QgsRasterDataProvider, QgsRasterShader
from qgis.gui import (
    QgsDockWidget, QgsMapLayerComboBox, QgsCollapsibleGroupBox, QgsColorRampButton
)
from rasterlayerstylingapp.rasterlayerstylingbandwidget import RasterLayerStylingBandWidget
from rasterlayerstylingapp.rasterlayerstylingpercentileswidget import RasterLayerStylingPercentilesWidget
from typeguard import typechecked


@typechecked
class RasterLayerStylingPanel(QgsDockWidget):
    # main layer
    mInfo: QLabel
    mLayer: QgsMapLayerComboBox
    mRefresh: QToolButton

    # renderer
    mRenderer: QTabWidget
    mVisualization: QComboBox
    mPseudoColorRamp: QgsColorRampButton
    mRedBand: RasterLayerStylingBandWidget
    mGreenBand: RasterLayerStylingBandWidget
    mBlueBand: RasterLayerStylingBandWidget
    mGrayBand: RasterLayerStylingBandWidget
    mPseudoBand: RasterLayerStylingBandWidget

    # linked layers
    mAddLink: QToolButton
    mRemoveLink: QToolButton
    mLinkedLayers: QTableWidget

    # min / max value settings
    mMinMaxUser: QCheckBox
    mMinMaxPercentile: QCheckBox
    mP1: QDoubleSpinBox
    mP2: QDoubleSpinBox
    mExtent: QComboBox
    mAccuracy: QComboBox
    mApply: QToolButton

    mGroupBoxMinMax: QgsCollapsibleGroupBox

    RgbRendererTab, GrayRendererTab, PseudoRendererTab, DefaultRendererTab, SpectralLinkingTab = range(5)
    BandLinkage, WavelengthLinkage = range(2)
    UserDefinedStretch, CumulativeCountCutStrech, ReferenceLayerStrech = range(3)
    WholeRasterStatistics, CurrentCanvasStatistics = range(2)
    EstimatedAccuracy, ActualAccuracy = range(2)

    def __init__(self, enmapBox: EnMAPBox, parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)
        self.enmapBox = enmapBox
        self.originalRenderer: Optional[QgsRasterRenderer] = None
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mLayer.setExcludedProviders(['wms'])
        self.cache = dict()

        self.visibilityChanged.connect(self.onPanelVisibilityChanged)

        self.enmapBox.currentLayerChanged.connect(self.mLayer.setLayer)
        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mRefresh.clicked.connect(self.onLayerChanged)

        self.mRenderer.currentChanged.connect(self.onRendererTabChanged)

        # renderer bands
        self.mVisualization.currentIndexChanged.connect(self.onVisualizationChanged)
        self.mPseudoColorRamp.setColorRampFromName('Spectral')
        self.mPseudoColorRamp.colorRampChanged.connect(self.updateRenderer)
        for mBand, name in [
            (self.mRedBand, 'Red\nband'), (self.mGreenBand, 'Green\nband'), (self.mBlueBand, 'Blue\nband'),
            (self.mGrayBand, 'Gray\nband'), (self.mPseudoBand, 'Band')
        ]:
            mBand.mName.setText(name)
            mBand.mMin.textChanged.connect(self.updateRenderer)
            mBand.mMax.textChanged.connect(self.updateRenderer)
            mBand.mSlider.valueChanged.connect(mBand.mBandNo.setBand)
            mBand.mBandNo.bandChanged.connect(mBand.mSlider.setValue)
            mBand.mBandNo.bandChanged.connect(self.onBandChanged)
            mBand.mIsBadBand.toggled.connect(self.onIsBadBandToggled)

            # waveband buttons
            for sname in CreateSpectralIndicesAlgorithm.ShortNames:
                lname = CreateSpectralIndicesAlgorithm.LongNameMapping[sname]
                wavelength, fwhm = CreateSpectralIndicesAlgorithm.WavebandMapping[sname]
                mWaveband: QToolButton = getattr(mBand, 'mWaveband' + sname)
                mWaveband.setToolTip(f'{lname} at {wavelength} Nanometers')
                mWaveband.clicked.connect(self.onWavebandClicked)

        # min / max value settings
        self.mP1.valueChanged.connect(self.updateMinMax)
        self.mP2.valueChanged.connect(self.updateMinMax)
        self.mExtent.currentIndexChanged.connect(self.onStatisticsChanged)
        self.mAccuracy.currentIndexChanged.connect(self.onStatisticsChanged)
        self.mApply.clicked.connect(self.updateMinMax)

        # spectral linking
        self.mAddLink.clicked.connect(self.onAddLinkClicked)
        self.mRemoveLink.clicked.connect(self.onRemoveLinkClicked)

        self.openedStateChanged.connect(self.onOpenStateChanged)

        # init GUI
        self.mRenderer.setCurrentIndex(self.DefaultRendererTab)

    def onOpenStateChanged(self, wasOpened: bool):
        panel: DockPanelUI = self.enmapBox.ui.dockPanel
        panel.mRasterLayerStyling.setChecked(wasOpened)

    def onRemoveLinkClicked(self):
        rows = [index.row() for index in self.mLinkedLayers.selectionModel().selectedRows()]
        if len(rows) == 0:
            rows = [self.mLinkedLayers.rowCount() - 1]
        self.mLinkedLayers.removeRow(rows[-1])

    def onAddLinkClicked(self):
        self.mLinkedLayers.setRowCount(self.mLinkedLayers.rowCount() + 1)
        row = self.mLinkedLayers.rowCount() - 1

        w = QgsMapLayerComboBox()  # raster layer
        w.setFilters(QgsMapLayerProxyModel.RasterLayer)
        w.setAllowEmptyLayer(True)
        w.setLayer(None)
        w.row = row
        self.mLinkedLayers.setCellWidget(row, 0, w)

        w = QComboBox()  # linkage
        w.addItems(['Band', 'Wavelength'])
        w.setCurrentIndex(1)
        self.mLinkedLayers.setCellWidget(row, 1, w)

        w = QComboBox()  # stretch type
        w.addItems(['User defined', 'Cumulative count cut', 'Reference layer'])
        w.setCurrentIndex(1)
        self.mLinkedLayers.setCellWidget(row, 2, w)

        w = RasterLayerStylingPercentilesWidget()  # percentiles
        self.mLinkedLayers.setCellWidget(row, 3, w)

        w = QLineEdit()  # red min
        w.setFrame(False)
        self.mLinkedLayers.setCellWidget(row, 4, w)
        w = QLineEdit()  # red max
        w.setFrame(False)
        self.mLinkedLayers.setCellWidget(row, 5, w)
        w = QLineEdit()  # green min
        w.setFrame(False)
        self.mLinkedLayers.setCellWidget(row, 6, w)
        w = QLineEdit()  # green max
        w.setFrame(False)
        self.mLinkedLayers.setCellWidget(row, 7, w)
        w = QLineEdit()  # blue min
        w.setFrame(False)
        self.mLinkedLayers.setCellWidget(row, 8, w)
        w = QLineEdit()  # blue max
        w.setFrame(False)
        self.mLinkedLayers.setCellWidget(row, 9, w)

        w = QComboBox()  # statistics
        w.addItems(['Whole raster', 'Current canvas'])
        w.setCurrentIndex(0)
        self.mLinkedLayers.setCellWidget(row, 10, w)

        w = QComboBox()  # accuracy
        w.addItems(['Estimated (faster)', 'Actual (slower)'])
        w.setCurrentIndex(0)
        self.mLinkedLayers.setCellWidget(row, 11, w)

    def updateGui(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()

        # set waveband enabled state
        availableShortNames = dict()
        for sname in CreateSpectralIndicesAlgorithm.ShortNames:

            # let's cache the broad band matching, because it takes a second
            cacheKey = layer.source(), sname
            if cacheKey not in self.cache:
                bandNo = CreateSpectralIndicesAlgorithm.findBroadBand(layer, sname, strict=True)
                isWaveband = bandNo is not None
                self.cache[cacheKey] = isWaveband, bandNo
            isWaveband, bandNo = self.cache[cacheKey]

            for mBand in [self.mRedBand, self.mGreenBand, self.mBlueBand, self.mGrayBand, self.mPseudoBand]:
                mWaveband: QToolButton = getattr(mBand, 'mWaveband' + sname)
                mWaveband.setVisible(isWaveband)

            if isWaveband:
                availableShortNames[sname] = bandNo

        # set rgb visualizations
        visualizations = CreateSpectralIndicesAlgorithm.filterVisualizations(
            CreateSpectralIndicesAlgorithm.sentinel2Visualizations(), list(availableShortNames.keys())
        )
        self.mVisualization.clear()
        items = [''] + [f'{name} ({"-".join(snames)})' for name, snames in visualizations.items()]
        self.mVisualization.addItems(items)

        # update wavelength info
        for mBand in [self.mRedBand, self.mGreenBand, self.mBlueBand, self.mGrayBand, self.mPseudoBand]:
            self.updateWavelengthInfo(mBand)

        # update is bad band
        for mBand in [self.mRedBand, self.mGreenBand, self.mBlueBand, self.mGrayBand, self.mPseudoBand]:
            self.updateIsBadBand(mBand)

    def onVisualizationChanged(self):
        if self.mVisualization.currentText() == '':
            return
        name, snames = self.mVisualization.currentText().split(' (')
        for sname, mBand in zip(
                snames.strip(' )').split('-'), [self.mRedBand, self.mGreenBand, self.mBlueBand]
        ):
            mWaveband: QToolButton = getattr(mBand, 'mWaveband' + sname)
            mWaveband.click()

    def onPanelVisibilityChanged(self):
        self.onLayerChanged()  # trigger GUI initialization

    def onWavebandClicked(self):
        mWaveband: QToolButton = self.sender()
        mBand: RasterLayerStylingBandWidget = mWaveband.parent()
        _, sname = mWaveband.objectName().split('Waveband')
        wavelength, fwhm = CreateSpectralIndicesAlgorithm.WavebandMapping[sname]
        reader = RasterReader(self.mLayer.currentLayer())
        bandNo = reader.findWavelength(wavelength)
        mBand.mBandNo.setBand(bandNo)

    def onEnmapBoxCurrentLayerChanged(self):
        if self.isHidden():
            return

        self.mLayer.setLayer(self.enmapBox.currentLayer())

    def onLayerChanged(self):

        if self.isHidden():  # do nothing if panel is hidden
            return

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if not isinstance(layer, QgsRasterLayer) or layer.dataProvider().name() in ['wms']:
            self.disableGui()
            return

        try:
            layer.rendererChanged.disconnect(self.onLayerRendererChanged)
        except Exception:
            pass
        layer.rendererChanged.connect(self.onLayerRendererChanged)

        self.originalRenderer = layer.renderer().clone()

        self.updateRendererTab(layer)
        self.onRendererTabChanged()

        self.enableGui()
        self.updateGui()

    def updateRendererTab(self, layer):
        with BlockSignals(self.mRenderer):
            renderer = layer.renderer()

            if isinstance(renderer, QgsMultiBandColorRenderer):
                self.mRenderer.setCurrentIndex(0)
            elif isinstance(renderer, QgsSingleBandGrayRenderer):
                self.mRenderer.setCurrentIndex(1)
            elif isinstance(renderer, QgsSingleBandPseudoColorRenderer):
                self.mRenderer.setCurrentIndex(2)
            else:
                self.mRenderer.setCurrentIndex(3)

    def onRendererTabChanged(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()

        if layer is None:
            return

        if self.mRenderer.currentIndex() == self.RgbRendererTab:
            for mBand in [self.mRedBand, self.mGreenBand, self.mBlueBand]:
                mBand.mBandNo.setLayer(layer)
                mBand.mSlider.setRange(1, layer.bandCount())

            renderer: QgsMultiBandColorRenderer = layer.renderer()
            if not isinstance(layer.renderer(), QgsMultiBandColorRenderer):
                if isinstance(self.originalRenderer, QgsMultiBandColorRenderer):
                    renderer = self.originalRenderer.clone()
                else:
                    renderer = Utils.multiBandColorRenderer(layer.dataProvider(), [1] * 3, [nan] * 3, [nan] * 3)
                layer.setRenderer(renderer)

            for mBand, ce, bandNo in [
                (self.mRedBand, renderer.redContrastEnhancement(), renderer.redBand()),
                (self.mGreenBand, renderer.greenContrastEnhancement(), renderer.greenBand()),
                (self.mBlueBand, renderer.blueContrastEnhancement(), renderer.blueBand())
            ]:
                with BlockSignals(mBand.mMin, mBand.mMax, mBand.mBandNo):
                    mBand.mMin.setText(str(ce.minimumValue()))
                    mBand.mMax.setText(str(ce.maximumValue()))
                    mBand.mBandNo.setBand(bandNo)

        elif self.mRenderer.currentIndex() == self.GrayRendererTab:
            self.mGrayBand.mBandNo.setLayer(layer)
            self.mGrayBand.mSlider.setRange(1, layer.bandCount())

            renderer: QgsSingleBandGrayRenderer = layer.renderer()
            if not isinstance(layer.renderer(), QgsSingleBandGrayRenderer):
                if isinstance(self.originalRenderer, QgsSingleBandGrayRenderer):
                    renderer = self.originalRenderer.clone()
                else:
                    renderer = Utils.singleBandGrayRenderer(layer.dataProvider(), 1, nan, nan)
                layer.setRenderer(renderer)
            ce: QgsContrastEnhancement = renderer.contrastEnhancement()

            with BlockSignals(self.mGrayBand.mMin, self.mGrayBand.mMax, self.mGrayBand.mBandNo):
                self.mGrayBand.mMin.setText(str(ce.minimumValue()))
                self.mGrayBand.mMax.setText(str(ce.maximumValue()))
                self.mGrayBand.mBandNo.setBand(renderer.grayBand())

        elif self.mRenderer.currentIndex() == self.PseudoRendererTab:
            self.mPseudoBand.mBandNo.setLayer(layer)
            self.mPseudoBand.mSlider.setRange(1, layer.bandCount())

            renderer: QgsSingleBandPseudoColorRenderer = layer.renderer()
            if not isinstance(layer.renderer(), QgsSingleBandPseudoColorRenderer):
                if isinstance(self.originalRenderer, QgsSingleBandPseudoColorRenderer):
                    renderer = self.originalRenderer.clone()
                else:
                    renderer = Utils.singleBandPseudoColorRenderer(layer.dataProvider(), 1, nan, nan, None)
                layer.setRenderer(renderer)
            shader: QgsRasterShader = renderer.shader()

            with BlockSignals(self.mPseudoBand.mMin, self.mPseudoBand.mMax, self.mPseudoBand.mBandNo):
                self.mPseudoBand.mMin.setText(str(shader.minimumValue()))
                self.mPseudoBand.mMax.setText(str(shader.maximumValue()))
                self.mPseudoBand.mBandNo.setBand(renderer.band())

        elif self.mRenderer.currentIndex() == self.DefaultRendererTab:
            layer.setRenderer(self.originalRenderer.clone())
        elif self.mRenderer.currentIndex() == self.SpectralLinkingTab:
            pass
        else:
            raise ValueError()

        # update bad band
        for mBand in [self.mRedBand, self.mGreenBand, self.mBlueBand, self.mGrayBand, self.mPseudoBand]:
            self.updateIsBadBand(mBand)

        if self.mRenderer.currentIndex() < self.DefaultRendererTab:
            self.mGroupBoxMinMax.show()
        else:
            self.mGroupBoxMinMax.hide()

        self.updateMinMax()
        self.updateRenderer()

    def onStatisticsChanged(self):
        if self.mRenderer.currentIndex() == self.RgbRendererTab:
            for mBand in [self.mRedBand, self.mGreenBand, self.mBlueBand]:
                mBand.mBandNo.bandChanged.emit(mBand.mBandNo.currentBand())
        elif self.mRenderer.currentIndex() == self.GrayRendererTab:
            self.mGrayBand.mBandNo.bandChanged.emit(self.mGrayBand.mBandNo.currentBand())
        elif self.mRenderer.currentIndex() == self.PseudoRendererTab:
            self.mPseudoBand.mBandNo.bandChanged.emit(self.mPseudoBand.mBandNo.currentBand())
        else:
            raise ValueError()

    def onBandChanged(self):

        mBand: RasterLayerStylingBandWidget = self.sender().parent()

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        bandNo = mBand.mBandNo.currentBand()

        # Check if renderer type was changed externally.
        # If so, create a new renderer with correct type.
        if self.mRenderer.currentIndex() == self.RgbRendererTab:
            if not isinstance(layer.renderer(), QgsMultiBandColorRenderer):
                renderer = Utils.multiBandColorRenderer(layer.dataProvider(), [bandNo] * 3, [nan] * 3, [nan] * 3)
                layer.setRenderer(renderer)
        elif self.mRenderer.currentIndex() == self.GrayRendererTab:
            if not isinstance(layer.renderer(), QgsSingleBandGrayRenderer):
                renderer = Utils.singleBandGrayRenderer(layer.dataProvider(), bandNo, nan, nan)
                layer.setRenderer(renderer)
        elif self.mRenderer.currentIndex() == self.PseudoRendererTab:
            if not isinstance(layer.renderer(), QgsSingleBandPseudoColorRenderer):
                renderer = Utils.singleBandPseudoColorRenderer(layer.dataProvider(), bandNo, nan, nan, None)
                layer.setRenderer(renderer)
        else:
            raise ValueError()

        self.updateWavelengthInfo(mBand)
        self.updateIsBadBand(mBand)
        self.updateMinMax()
        self.updateRenderer()

    def onIsBadBandToggled(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        mIsBadBand: QCheckBox = self.sender()
        mBand: RasterLayerStylingBandWidget = mIsBadBand.parent()
        bandNo = mBand.mBandNo.currentBand()
        if bandNo == -1:
            return

        if mIsBadBand.isChecked():
            badBandMultiplier = 0
        else:
            badBandMultiplier = 1

        source = layer.source()

        # find all layers with same source
        layers = list()
        for layerId in QgsProject.instance().mapLayers():
            aLayer = QgsProject.instance().mapLayer(layerId)
            if not isinstance(aLayer, QgsRasterLayer):
                continue
            if aLayer.dataProvider().name() != 'gdal':
                continue
            if source.replace(r'\/', '') == aLayer.source().replace(r'\/', ''):
                layers.append(aLayer)

        # flush sources
        for aLayer in layers:
            Utils.setLayerDataSource(aLayer, 'gdal', source)

        # set metadata
        ds: gdal.Dataset = gdal.Open(source)
        writer = RasterWriter(ds)
        writer.setBadBandMultiplier(badBandMultiplier, bandNo)
        writer.close()
        del ds

        # reconnect sources
        for aLayer in layers:
            Utils.setLayerDataSource(aLayer, 'gdal', source)

    def onLayerRendererChanged(self):
        # the renderer of the layer may be changed from outside, so we need to update the settings

        if self.isHidden():  # do nothing if panel is hidden
            return

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is not self.sender():
            return

        renderer = layer.renderer()
        if isinstance(renderer, QgsMultiBandColorRenderer):
            with BlockSignals(self.mRedBand, self.mGreenBand, self.mBlueBand):
                self.mRedBand.mBandNo.setBand(renderer.redBand())
                self.mGreenBand.mBandNo.setBand(renderer.greenBand())
                self.mBlueBand.mBandNo.setBand(renderer.blueBand())
        elif isinstance(renderer, QgsSingleBandGrayRenderer):
            with BlockSignals(self.mGrayBand):
                self.mGrayBand.mBandNo.setBand(renderer.grayBand())
        elif isinstance(renderer, QgsSingleBandPseudoColorRenderer):
            with BlockSignals(self.mPseudoBand.mBandNo):
                self.mPseudoBand.mBandNo.setBand(renderer.band())
        else:
            pass

    def updateWavelengthInfo(self, mBand: RasterLayerStylingBandWidget):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return
        bandNo = mBand.mBandNo.currentBand()
        if bandNo == -1:
            wavelength = None
        elif bandNo > layer.bandCount():
            wavelength = None
        else:
            wavelength = RasterReader(layer).wavelength(bandNo)
        if wavelength is None:
            mBand.mWavelength.hide()
        else:
            mBand.mWavelength.show()
            mBand.mWavelength.setValue(int(wavelength))

    def updateIsBadBand(self, mBand: RasterLayerStylingBandWidget):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return
        bandNo = mBand.mBandNo.currentBand()
        if bandNo == -1:
            mBand.mIsBadBand.hide()
        else:
            mBand.mIsBadBand.show()
            if RasterReader(layer).badBandMultiplier(bandNo) == 0:
                mBand.mIsBadBand.setChecked(True)
            else:
                mBand.mIsBadBand.setChecked(False)

    def updateMinMax(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        def setCumulativeCut(bandNo: int, mBandMin: QLineEdit, mBandMax: QLineEdit):
            vmin, vmax = layer.dataProvider().cumulativeCut(
                bandNo, self.mP1.value() / 100., self.mP2.value() / 100.,
                self.currentExtent(layer, self.mExtent.currentIndex()),
                self.currentSampleSize(self.mAccuracy.currentIndex())
            )

            with BlockSignals(mBandMin, mBandMax):
                mBandMin.setText(str(vmin))
                mBandMax.setText(str(vmax))

        if self.mRenderer.currentIndex() == self.RgbRendererTab:
            if self.mMinMaxPercentile.isChecked():
                for mBand in [self.mRedBand, self.mGreenBand, self.mBlueBand]:
                    setCumulativeCut(mBand.mBandNo.currentBand(), mBand.mMin, mBand.mMax)
        elif self.mRenderer.currentIndex() == self.GrayRendererTab:
            if self.mMinMaxPercentile.isChecked():
                setCumulativeCut(self.mGrayBand.mBandNo.currentBand(), self.mGrayBand.mMin, self.mGrayBand.mMax)
        elif self.mRenderer.currentIndex() == self.PseudoRendererTab:
            if self.mMinMaxPercentile.isChecked():
                setCumulativeCut(self.mPseudoBand.mBandNo.currentBand(), self.mPseudoBand.mMin, self.mPseudoBand.mMax)
        elif self.mRenderer.currentIndex() >= self.DefaultRendererTab:
            pass
        else:
            raise ValueError()

        self.updateRenderer()

    def updateRenderer(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        if self.mRenderer.currentIndex() == self.RgbRendererTab:
            renderer: QgsMultiBandColorRenderer = layer.renderer()
            for mBand, ce, setBand in [
                (self.mRedBand, renderer.redContrastEnhancement(), renderer.setRedBand),
                (self.mGreenBand, renderer.greenContrastEnhancement(), renderer.setGreenBand),
                (self.mBlueBand, renderer.blueContrastEnhancement(), renderer.setBlueBand),
            ]:
                bandNo = mBand.mBandNo.currentBand()
                setBand(bandNo)
                ce.setMinimumValue(tofloat(mBand.mMin.text()))
                ce.setMaximumValue(tofloat(mBand.mMax.text()))
        elif self.mRenderer.currentIndex() == self.GrayRendererTab:
            bandNo = self.mGrayBand.mBandNo.currentBand()
            renderer: QgsSingleBandGrayRenderer = layer.renderer()
            renderer.setGrayBand(bandNo)
            ce = renderer.contrastEnhancement()
            ce.setMinimumValue(tofloat(self.mGrayBand.mMin.text()))
            ce.setMaximumValue(tofloat(self.mGrayBand.mMax.text()))
        elif self.mRenderer.currentIndex() == self.PseudoRendererTab:
            bandNo = self.mPseudoBand.mBandNo.currentBand()
            minValue = tofloat(self.mPseudoBand.mMin.text())
            maxValue = tofloat(self.mPseudoBand.mMax.text())
            ramp = self.mPseudoColorRamp.colorRamp()
            renderer = Utils.singleBandPseudoColorRenderer(
                layer.dataProvider(), bandNo, minValue, maxValue, ramp
            )
            layer.setRenderer(renderer)
        elif self.mRenderer.currentIndex() >= self.DefaultRendererTab:
            pass
        else:
            raise ValueError()

        layer.rendererChanged.emit()
        layer.triggerRepaint()
        self.updateLinkedLayerRenderer()

    def updateLinkedLayerRenderer(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        for row in range(self.mLinkedLayers.rowCount()):
            # get user settings
            w: QgsMapLayerComboBox = self.mLinkedLayers.cellWidget(row, 0)
            layer2: QgsRasterLayer = w.currentLayer()
            if layer2 is None:
                continue
            if layer2 is layer:
                continue
            provider2: QgsRasterDataProvider = layer2.dataProvider()

            w: QComboBox = self.mLinkedLayers.cellWidget(row, 1)
            linkageType = w.currentIndex()

            w: QComboBox = self.mLinkedLayers.cellWidget(row, 2)
            stretchType = w.currentIndex()

            w: RasterLayerStylingPercentilesWidget = self.mLinkedLayers.cellWidget(row, 3)
            p1 = w.mP1.value()
            p2 = w.mP2.value()

            w: QLineEdit = self.mLinkedLayers.cellWidget(row, 4)
            redMin = tofloat(w.text())
            w: QLineEdit = self.mLinkedLayers.cellWidget(row, 5)
            redMax = tofloat(w.text())
            w: QLineEdit = self.mLinkedLayers.cellWidget(row, 6)
            greenMin = tofloat(w.text())
            w: QLineEdit = self.mLinkedLayers.cellWidget(row, 7)
            greenMax = tofloat(w.text())
            w: QLineEdit = self.mLinkedLayers.cellWidget(row, 8)
            blueMin = tofloat(w.text())
            w: QLineEdit = self.mLinkedLayers.cellWidget(row, 9)
            blueMax = tofloat(w.text())

            w: QComboBox = self.mLinkedLayers.cellWidget(row, 10)
            statisticsType = w.currentIndex()

            w: QComboBox = self.mLinkedLayers.cellWidget(row, 11)
            accuracyType = w.currentIndex()

            # update renderer
            reader = RasterReader(layer2)
            if self.mRenderer.currentIndex() == self.RgbRendererTab:
                redWavelength = self.mRedBand.mWavelength.value()
                greenWavelength = self.mGreenBand.mWavelength.value()
                blueWavelength = self.mBlueBand.mWavelength.value()

                if linkageType == self.BandLinkage:
                    redBandNo = min(self.mRedBand.mBandNo.currentBand(), reader.bandCount())
                    greenBandNo = min(self.mGreenBand.mBandNo.currentBand(), reader.bandCount())
                    blueBandNo = min(self.mBlueBand.mBandNo.currentBand(), reader.bandCount())
                elif linkageType == self.WavelengthLinkage:
                    redBandNo = reader.findWavelength(redWavelength)
                    if redBandNo is None:
                        redBandNo = 1
                    greenBandNo = reader.findWavelength(greenWavelength)
                    if greenBandNo is None:
                        greenBandNo = 1
                    blueBandNo = reader.findWavelength(blueWavelength)
                    if blueBandNo is None:
                        blueBandNo = 1
                else:
                    raise ValueError()
                renderer: QgsMultiBandColorRenderer = layer.renderer()

                if stretchType == self.UserDefinedStretch:
                    pass
                elif stretchType == self.CumulativeCountCutStrech:
                    redMin, redMax = layer2.dataProvider().cumulativeCut(
                        redBandNo, p1 / 100., p2 / 100., self.currentExtent(layer2, statisticsType),
                        self.currentSampleSize(accuracyType)
                    )
                    greenMin, greenMax = layer2.dataProvider().cumulativeCut(
                        greenBandNo, p1 / 100., p2 / 100., self.currentExtent(layer2, statisticsType),
                        self.currentSampleSize(accuracyType)
                    )
                    blueMin, blueMax = layer2.dataProvider().cumulativeCut(
                        blueBandNo, p1 / 100., p2 / 100., self.currentExtent(layer2, statisticsType),
                        self.currentSampleSize(accuracyType)
                    )

                elif stretchType == self.ReferenceLayerStrech:
                    ce: QgsContrastEnhancement = renderer.redContrastEnhancement()
                    redMin = ce.minimumValue()
                    redMax = ce.maximumValue()
                    ce: QgsContrastEnhancement = renderer.greenContrastEnhancement()
                    greenMin = ce.minimumValue()
                    greenMax = ce.maximumValue()
                    ce: QgsContrastEnhancement = renderer.blueContrastEnhancement()
                    blueMin = ce.minimumValue()
                    blueMax = ce.maximumValue()

                else:
                    raise ValueError()

                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 4)
                w.setText(str(tofloat(redMin)))
                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 5)
                w.setText(str(tofloat(redMax)))
                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 6)
                w.setText(str(tofloat(greenMin)))
                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 7)
                w.setText(str(tofloat(greenMax)))
                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 8)
                w.setText(str(tofloat(blueMin)))
                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 9)
                w.setText(str(tofloat(blueMax)))

                renderer2 = renderer.clone()
                renderer2.setRedBand(redBandNo)
                renderer2.setGreenBand(greenBandNo)
                renderer2.setBlueBand(blueBandNo)

                ce2 = QgsContrastEnhancement(provider2.dataType(redBandNo))
                ce2.setMinimumValue(redMin)
                ce2.setMaximumValue(redMax)
                ce2.setContrastEnhancementAlgorithm(
                    QgsContrastEnhancement.ContrastEnhancementAlgorithm.StretchToMinimumMaximum
                )
                renderer2.setRedContrastEnhancement(ce2)
                ce2 = QgsContrastEnhancement(provider2.dataType(greenBandNo))
                ce2.setMinimumValue(greenMin)
                ce2.setMaximumValue(greenMax)
                ce2.setContrastEnhancementAlgorithm(
                    QgsContrastEnhancement.ContrastEnhancementAlgorithm.StretchToMinimumMaximum
                )
                renderer2.setGreenContrastEnhancement(ce2)
                ce2 = QgsContrastEnhancement(provider2.dataType(blueBandNo))
                ce2.setMinimumValue(blueMin)
                ce2.setMaximumValue(blueMax)
                ce2.setContrastEnhancementAlgorithm(
                    QgsContrastEnhancement.ContrastEnhancementAlgorithm.StretchToMinimumMaximum
                )
                renderer2.setBlueContrastEnhancement(ce2)
                layer2.setRenderer(renderer2)

            elif self.mRenderer.currentIndex() == self.GrayRendererTab:
                wavelength = self.mGrayBand.mWavelength.value()
                if linkageType == self.BandLinkage:
                    bandNo = min(self.mGrayBand.mBandNo.currentBand(), reader.bandCount())
                elif linkageType == self.WavelengthLinkage:
                    bandNo = reader.findWavelength(wavelength)
                    if bandNo is None:
                        bandNo = 1
                else:
                    raise ValueError()
                renderer: QgsSingleBandGrayRenderer = layer.renderer()

                if stretchType == self.UserDefinedStretch:
                    pass
                elif stretchType == self.CumulativeCountCutStrech:
                    redMin, redMax = layer2.dataProvider().cumulativeCut(
                        bandNo, p1 / 100., p2 / 100., self.currentExtent(layer2, statisticsType),
                        self.currentSampleSize(accuracyType)
                    )

                elif stretchType == self.ReferenceLayerStrech:
                    ce: QgsContrastEnhancement = renderer.contrastEnhancement()
                    redMin = ce.minimumValue()
                    redMax = ce.maximumValue()
                else:
                    raise ValueError()

                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 4)
                w.setText(str(tofloat(redMin)))
                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 5)
                w.setText(str(tofloat(redMax)))

                renderer2 = renderer.clone()
                renderer2.setGrayBand(bandNo)
                ce2 = QgsContrastEnhancement(provider2.dataType(bandNo))
                ce2.setMinimumValue(redMin)
                ce2.setMaximumValue(redMax)
                ce2.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
                renderer2.setContrastEnhancement(ce2)
                layer2.setRenderer(renderer2)
            elif self.mRenderer.currentIndex() == self.PseudoRendererTab:
                wavelength = self.mPseudoBand.mWavelength.value()
                if linkageType == self.BandLinkage:
                    bandNo = min(self.mPseudoBand.mBandNo.currentBand(), reader.bandCount())
                elif linkageType == self.WavelengthLinkage:
                    bandNo = reader.findWavelength(wavelength)
                    if bandNo is None:
                        bandNo = 1
                else:
                    raise ValueError()
                renderer: QgsSingleBandPseudoColorRenderer = layer.renderer()

                if stretchType == self.UserDefinedStretch:
                    pass
                elif stretchType == self.CumulativeCountCutStrech:
                    redMin, redMax = layer2.dataProvider().cumulativeCut(
                        bandNo, p1 / 100., p2 / 100., self.currentExtent(layer2, statisticsType),
                        self.currentSampleSize(accuracyType)
                    )
                elif stretchType == self.ReferenceLayerStrech:
                    shader: QgsRasterShader = renderer.shader()
                    redMin = shader.minimumValue()
                    redMax = shader.maximumValue()
                else:
                    raise ValueError()

                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 4)
                w.setText(str(tofloat(redMin)))
                w: QLineEdit = self.mLinkedLayers.cellWidget(row, 5)
                w.setText(str(tofloat(redMax)))
                ramp = self.mPseudoColorRamp.colorRamp()
                renderer2 = Utils.singleBandPseudoColorRenderer(provider2, bandNo, redMin, redMax, ramp)
                layer2.setRenderer(renderer2)
            elif self.mRenderer.currentIndex() == self.DefaultRendererTab:
                pass
            elif self.mRenderer.currentIndex() == self.SpectralLinkingTab:
                pass
            else:
                raise ValueError()

            layer.rendererChanged.emit()
            layer2.triggerRepaint()

    def currentExtent(self, layer: QgsRasterLayer, statisticsType: int) -> QgsRectangle:

        if statisticsType == self.WholeRasterStatistics:
            return layer.extent()
        elif statisticsType == self.CurrentCanvasStatistics:
            mapCanvas = self.currentMapCanvas(layer)
            return SpatialExtent(mapCanvas.crs(), mapCanvas.extent()).toCrs(layer.crs())
        else:
            raise ValueError()

    def currentMapCanvas(self, layer: QgsRasterLayer) -> MapCanvas:

        for mapDock in self.enmapBox.dockManager().mapDocks():
            if layer in mapDock.mapCanvas().layers():
                return mapDock.mapCanvas()
        raise ValueError()

    def currentSampleSize(self, accuracyType: int) -> int:
        if accuracyType == self.EstimatedAccuracy:
            return int(QgsRasterLayer.SAMPLE_SIZE)
        elif accuracyType == self.ActualAccuracy:
            return 0  # use all pixel
        else:
            raise ValueError()

    def disableGui(self):
        self.mInfo.show()
        self.mRenderer.hide()
        self.mGroupBoxMinMax.hide()

    def enableGui(self):
        self.mInfo.hide()
        self.mRenderer.show()
        self.mGroupBoxMinMax.show()


# utils
def tofloat(text: str) -> float:
    try:
        return float(text)
    except Exception:
        return nan
