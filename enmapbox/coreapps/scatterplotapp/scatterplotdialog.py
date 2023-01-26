import warnings
from math import ceil, sqrt, floor
from os.path import join, exists
from random import getrandbits
from typing import Optional, Tuple, Dict

import numpy as np
from osgeo import gdal
from scipy.stats import binned_statistic_2d, pearsonr

from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import MarkerSymbolComboBox, MarkerSymbol
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph import PlotWidget, ImageItem, mkPen
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from processing import AlgorithmDialog
from qgis.PyQt.QtCore import QRectF, QPointF, Qt
from qgis.PyQt.QtGui import QMouseEvent, QColor
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QComboBox, QCheckBox, QDoubleSpinBox, QPlainTextEdit, QSpinBox
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsMapSettings, QgsStyle, QgsColorRamp, \
    QgsFieldProxyModel, QgsMapLayer
from qgis.gui import QgsMapLayerComboBox, QgsMapCanvas, QgsRasterBandComboBox, QgsColorButton, QgsColorRampButton, \
    QgsFilterLineEdit, QgsFieldComboBox
from typeguard import typechecked


@typechecked
class ScatterPlotWidget(PlotWidget):

    def __init__(self, *args, **kwargs):
        PlotWidget.__init__(self, *args, **kwargs, background='#000')

    def mousePressEvent(self, ev):
        self.autoRange()

    def mouseMoveEvent(self, ev):
        self.autoRange()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.autoRange()

    def wheelEvent(self, ev):
        self.autoRange()


@typechecked
class ScatterPlotDialog(QMainWindow):
    mLayerX: QgsMapLayerComboBox
    mLayerY: QgsMapLayerComboBox
    mGrid: QgsMapLayerComboBox
    mBandX: QgsRasterBandComboBox
    mBandY: QgsRasterBandComboBox
    mFieldY: QgsFieldComboBox

    mScatterPlot: ScatterPlotWidget

    mMinimumX: QgsFilterLineEdit
    mMaximumX: QgsFilterLineEdit
    mMinimumY: QgsFilterLineEdit
    mMaximumY: QgsFilterLineEdit
    mSwapAxes: QCheckBox
    mColoringType: QComboBox
    mColoringRamp: QgsColorRampButton
    mColoringColor: QgsColorButton
    mColoringSymbol: MarkerSymbolComboBox
    mColoringSymbolSize: QSpinBox
    mDensityP1: QDoubleSpinBox
    mDensityP2: QDoubleSpinBox

    mExtent: QComboBox
    mAccuracy: QComboBox

    mOneToOneLine: QCheckBox
    mOneToOneLineColor: QgsColorButton
    mFittedLine: QCheckBox
    mFittedLineColor: QgsColorButton
    mFittedLineReport: QPlainTextEdit

    mLiveUpdate: QCheckBox
    mApply: QToolButton

    DensityColoring, ScatterColoring = 0, 1
    EstimatedAccuracy, ActualAccuracy = 0, 1
    WholeRasterExtent, CurrentCanvasExtent = 0, 1

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        # init gui
        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.mLayerX.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mFieldY.setFilters(QgsFieldProxyModel.Numeric)

        self.mMinimumX.clearValue()
        self.mMaximumX.clearValue()
        self.mMinimumY.clearValue()
        self.mMaximumY.clearValue()

        colorRamp: QgsColorRamp = QgsStyle().defaultStyle().colorRamp('Spectral')
        colorRamp.invert()
        self.mColoringRamp.setColorRamp(colorRamp)
        self.mFieldY.hide()
        self.mSwapAxes.hide()
        self.mColoringSymbol.setMarkerSymbol(MarkerSymbol.No_Symbol)

        # init data
        self.cache: Dict[str, QgsRasterLayer] = dict()

        # connect signals
        self.mLayerX.layerChanged.connect(self.onLayerXChanged)
        self.mLayerY.layerChanged.connect(self.onLayerYChanged)

        self.mBandX.bandChanged.connect(self.onLiveUpdate)
        self.mBandY.bandChanged.connect(self.onLiveUpdate)
        self.mFieldY.fieldChanged.connect(self.onFieldYChanged)
        self.mSwapAxes.toggled.connect(self.onLiveUpdate)

        self.mScatterPlot.sigDeviceRangeChanged.connect(self.onLiveUpdate)
        self.mMinimumX.textChanged.connect(self.onLiveUpdate)
        self.mMaximumX.textChanged.connect(self.onLiveUpdate)
        self.mMinimumY.textChanged.connect(self.onLiveUpdate)
        self.mMaximumY.textChanged.connect(self.onLiveUpdate)
        self.mColoringType.currentIndexChanged.connect(self.onLiveUpdate)
        self.mColoringRamp.colorRampChanged.connect(self.onLiveUpdate)
        self.mColoringColor.colorChanged.connect(self.onLiveUpdate)
        self.mColoringSymbol.currentIndexChanged.connect(self.onLiveUpdate)
        self.mColoringSymbolSize.valueChanged.connect(self.onLiveUpdate)
        self.mDensityP1.valueChanged.connect(self.onLiveUpdate)
        self.mDensityP2.valueChanged.connect(self.onLiveUpdate)

        self.mExtent.currentIndexChanged.connect(self.onLiveUpdate)
        self.mAccuracy.currentIndexChanged.connect(self.onLiveUpdate)

        self.mFittedLine.toggled.connect(self.onLiveUpdate)
        self.mOneToOneLine.toggled.connect(self.onLiveUpdate)
        self.mFittedLineColor.colorChanged.connect(self.onLiveUpdate)
        self.mOneToOneLineColor.colorChanged.connect(self.onLiveUpdate)

        self.mApply.clicked.connect(self.onApplyClicked)

    def currentLayerX(self) -> Optional[QgsRasterLayer]:
        return self.mLayerX.currentLayer()

    def currentLayerY(self) -> Optional[QgsMapLayer]:
        return self.mLayerY.currentLayer()

    def currentBandX(self) -> Optional[int]:
        if self.currentLayerX() is None:
            return None

        bandNoX = self.mBandX.currentBand()

        if bandNoX == -1:
            bandNoX = None

        return bandNoX

    def currentBandY(self) -> Optional[int]:
        layerY = self.currentLayerY()
        if not isinstance(layerY, QgsRasterLayer):
            return None

        bandNoY = self.mBandY.currentBand()

        if bandNoY == -1:
            bandNoY = None

        return bandNoY

    def currentFieldY(self) -> Optional[str]:
        fieldY = self.mFieldY.currentField()
        if fieldY == '':
            return None

        return fieldY

    def currentExtent(self) -> Optional[SpatialExtent]:
        layer = self.currentLayerX()
        if layer is None:
            return None

        if self.mExtent.currentIndex() == self.WholeRasterExtent:
            return SpatialExtent(layer.crs(), layer.extent())
        elif self.mExtent.currentIndex() == self.CurrentCanvasExtent:
            mapSettings: QgsMapSettings = self.mMapCanvas.mapSettings()
            return SpatialExtent(mapSettings.destinationCrs(), self.mMapCanvas.extent()).toCrs(layer.crs())
        else:
            raise ValueError()

    def parseRange(self, textLower: str, textUpper: str, array: np.ndarray) -> Tuple[float, float]:

        def tofloat(text: str) -> Optional[float]:
            try:
                return float(text)
            except Exception:
                return None

        lower = tofloat(textLower)
        upper = tofloat(textUpper)

        if lower is None:
            lower = np.min(array)
        if upper is None:
            upper = np.max(array)

        return float(lower), float(upper)

    def currentSampleSize(self) -> int:
        if self.mAccuracy.currentIndex() == self.EstimatedAccuracy:
            return int(QgsRasterLayer.SAMPLE_SIZE)
        elif self.mAccuracy.currentIndex() == self.ActualAccuracy:
            return 0  # use all pixel
        else:
            raise ValueError()

    def onLayerXChanged(self):

        # disconnect old map canvas
        if self.mMapCanvas is not None:
            try:
                self.mMapCanvas.extentsChanged.disconnect(self.onMapCanvasExtentsChanged)
            except Exception:
                pass

        # connect new map canvas
        self.mMapCanvas = None
        layer = self.currentLayerX()
        for mapDock in self.enmapBox.dockManager().mapDocks():
            if layer in mapDock.mapCanvas().layers():
                self.mMapCanvas = mapDock.mapCanvas()
                break
        if self.mMapCanvas is not None:
            self.mMapCanvas.extentsChanged.connect(self.onMapCanvasExtentsChanged)

        self.mBandX.setBand(-1)
        self.mLayerY.setLayer(None)

    def onLayerYChanged(self):

        layerY = self.currentLayerY()
        if isinstance(layerY, QgsRasterLayer):
            self.mBandY.show()
            self.mFieldY.hide()
            self.mSwapAxes.hide()
        else:
            self.mBandY.hide()
            self.mFieldY.show()
            self.mSwapAxes.show()
            self.mColoringType.setCurrentIndex(self.ScatterColoring)
            if self.mColoringSymbol.markerSymbol() == MarkerSymbol.No_Symbol:
                self.mColoringSymbol.setMarkerSymbol(MarkerSymbol.Plus)
            self.mAccuracy.setCurrentIndex(self.ActualAccuracy)

    def onFieldYChanged(self):
        # rasterize if needed
        layerX = self.currentLayerX()
        assert layerX is not None
        layerY = self.currentLayerY()
        fieldY = self.currentFieldY()
        if layerY is None or fieldY is None:
            return
        if isinstance(layerY, QgsRasterLayer):
            return

        key = layerX.source(), layerY.source(), fieldY
        if key not in self.cache:
            noDataValue = -9999
            alg = RasterizeVectorAlgorithm()
            filename = join(Utils.getTempDirInTempFolder(), str(getrandbits(128))) + '.tif'
            parameters = {
                alg.P_VECTOR: layerY,
                alg.P_GRID: layerX,
                alg.P_INIT_VALUE: noDataValue,
                alg.P_BURN_ATTRIBUTE: fieldY,
                alg.P_DATA_TYPE: alg.Float32,
                alg.P_OUTPUT_RASTER: filename
            }

            class Wrapper(AlgorithmDialog):
                def finish(self, successful, result, context, feedback, in_place=False):
                    super().finish(successful, result, context, feedback, in_place=False)
                    if successful:
                        self.close()

            self.enmapBox.showProcessingAlgorithmDialog(alg, parameters, True, True, Wrapper, True, self)
            if not exists(filename):
                self.mFieldY.setField('')
                return
            ds = gdal.Open(filename)
            writer = RasterWriter(ds)
            writer.setNoDataValue(noDataValue)
            writer.close()
            del writer
            layer = QgsRasterLayer(filename)
            self.cache[key] = layer

        self.onLiveUpdate()

    def onMapCanvasExtentsChanged(self):
        if self.mExtent.currentIndex() == self.WholeRasterExtent:
            return
        self.onLiveUpdate()

    def onApplyClicked(self):

        if self.isHidden():
            return

        layerX = self.currentLayerX()
        layerY = self.currentLayerY()

        if layerX is None or layerY is None:
            return

        bandNoX = self.currentBandX()
        if not isinstance(layerY, QgsRasterLayer):
            fieldY = self.currentFieldY()
            if fieldY is None:
                return
            key = layerX.source(), layerY.source(), fieldY
            assert key in self.cache
            layerY = self.cache[key]
            bandNoY = 1
            yIsVector = True
        else:
            bandNoY = self.currentBandY()
            yIsVector = False

        if bandNoX is None or bandNoY is None:
            return

        # derive sampling extent
        readerX = RasterReader(layerX)
        readerY = RasterReader(layerY)
        extent = self.currentExtent()
        extent = extent.intersect(readerX.extent())

        # derive sampling size
        width = extent.width() / readerX.rasterUnitsPerPixelX()
        height = extent.height() / readerX.rasterUnitsPerPixelY()
        width = max(min(int(round(width)), readerX.width()), 1)  # 1 <= width <= layerWidth
        height = max(min(int(round(height)), readerX.height()), 1)  # 1 <= height <= layerHeight

        sampleSize = self.currentSampleSize()
        if sampleSize != 0:
            sampleFraction = sqrt(min(sampleSize / (width * height), 1))
            width = ceil(width * sampleFraction)
            height = ceil(height * sampleFraction)

        # read data
        arrayX = readerX.arrayFromBoundingBoxAndSize(extent, width, height, [bandNoX])[0]
        arrayY = readerY.arrayFromBoundingBoxAndSize(extent, width, height, [bandNoY])[0]

        validX = readerX.maskArray([arrayX], [bandNoX])[0]
        validY = readerY.maskArray([arrayY], [bandNoY])[0]
        valid = np.all([validX, validY], axis=0)

        x = arrayX[valid]
        y = arrayY[valid]

        if self.mSwapAxes.isChecked() and yIsVector:
            x, y = y, x

        # calculate 2d histogram
        bins = self.mScatterPlot.getPlotItem().getViewBox().size()
        bins = floor(bins.width() * 0.9), floor(
            bins.height() * 0.9)  # used slightly coarser binning to avoid rendering artefacts (see issue #1407)

        if x.size == 0:
            self.mScatterPlot.clear()
            self.mScatterPlot.setRange(QRectF(0, 0, 1, 1))
            # self.mScatterPlot.autoRange()
            return

        range = [self.parseRange(self.mMinimumX.value(), self.mMaximumX.value(), x),
                 self.parseRange(self.mMinimumY.value(), self.mMaximumY.value(), y)]

        # update range
        if self.mMinimumX.isNull():
            self.mMinimumX.setNullValue(f'derived ({range[0][0]})')
            self.mMinimumX.clearValue()
            self.mMinimumX.deselect()
        if self.mMaximumX.isNull():
            self.mMaximumX.setNullValue(f'derived ({range[0][1]})')
            self.mMaximumX.clearValue()
            self.mMaximumX.deselect()
        if self.mMinimumY.isNull():
            self.mMinimumY.setNullValue(f'derived ({range[1][0]})')
            self.mMinimumY.clearValue()
            self.mMinimumY.deselect()
        if self.mMaximumY.isNull():
            self.mMaximumY.setNullValue(f'derived ({range[1][1]})')
            self.mMaximumY.clearValue()
            self.mMaximumY.deselect()

        try:  # use try-except to resolve issue #1408
            counts, x_edge, y_edge, binnumber = binned_statistic_2d(x, y, x, 'count', bins, range, True)
        except Exception:
            self.mScatterPlot.clear()
            return

        background = counts == 0

        # stretch counts
        lower, upper = np.percentile(counts[counts != 0], [self.mDensityP1.value(), self.mDensityP2.value()])
        span = upper - lower
        span = max(span, 1)  # avoid devision by zero
        counts = np.round((counts - lower) * (254 / span))
        counts = np.clip(counts, 0, 254).astype(np.uint8) + 1
        counts[background] = 0

        counts = counts.astype(float)
        counts[background] = np.nan

        # update plot
        self.mScatterPlot.clear()
        xmin, xmax = range[0]
        ymin, ymax = range[1]
        topLeft = QPointF(xmin, ymin)
        bottomRight = QPointF(xmax, ymax)
        rect = QRectF(topLeft, bottomRight)
        imageItem = ImageItem(counts)
        imageItem.setRect(rect)

        if self.mColoringType.currentIndex() == self.DensityColoring:
            lookupTable = utilsQgsColorRampToPyQtGraphLookupTable(self.mColoringRamp.colorRamp())
        elif self.mColoringType.currentIndex() == self.ScatterColoring:
            color = self.mColoringColor.color()
            lookupTable = np.empty(shape=(256, 4), dtype=np.uint8)
            lookupTable[:, 0] = color.red()
            lookupTable[:, 1] = color.green()
            lookupTable[:, 2] = color.blue()
            lookupTable[:, 3] = 255
        else:
            raise ValueError()
        lookupTable[0] = 0
        imageItem.setLookupTable(lookupTable)

        if self.mColoringType.currentIndex() == self.DensityColoring:
            self.mScatterPlot.addItem(imageItem)
        elif self.mColoringType.currentIndex() == self.ScatterColoring:
            symbol = self.mColoringSymbol.markerSymbol()
            if symbol == MarkerSymbol.No_Symbol:
                self.mScatterPlot.addItem(imageItem)
            else:
                color = self.mColoringColor.color()
                plotItem = self.mScatterPlot.plot(x, y)
                plotItem.setSymbol(symbol.value)
                plotItem.setSymbolBrush(color)
                plotItem.setSymbolPen(color)
                plotItem.setSymbolSize(self.mColoringSymbolSize.value())
                plotItem.setPen(None)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.mScatterPlot.addItem(plotItem)

        # analytics
        if self.mOneToOneLine.isChecked():
            plotItem = self.mScatterPlot.plot([xmin, xmax], [xmin, xmax])
            plotItem.setPen(mkPen(color=self.mOneToOneLineColor.color(), style=Qt.SolidLine))

        if self.mFittedLine.isChecked():
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            x_ = range[0]
            y_ = p(x_)
            plotItem = self.mScatterPlot.plot(x_, y_)
            plotItem.setPen(mkPen(color=self.mFittedLineColor.color(), style=Qt.SolidLine))

            r2 = round(pearsonr(x, y)[0] ** 2, 4)
            rmse = round(np.sqrt(np.mean((x - y) ** 2)), 4)
            text = f'f(x) = {str(p).strip()} | r^2 = {r2} | rmse = {rmse}'
            self.mFittedLineReport.setPlainText(text)

        self.mScatterPlot.autoRange()

    def onLiveUpdate(self):
        if not self.mLiveUpdate.isChecked():
            return

        self.onApplyClicked()


@typechecked
def utilsQgsColorRampToPyQtGraphLookupTable(colorRamp: QgsColorRamp) -> np.ndarray:
    array = np.empty(shape=(256, 4), dtype=np.uint8)
    for i in range(256):
        color = colorRamp.color(i / 255)
        assert isinstance(color, QColor)
        array[i, 0] = color.red()
        array[i, 1] = color.green()
        array[i, 2] = color.blue()
        array[i, 3] = 255
    return array
