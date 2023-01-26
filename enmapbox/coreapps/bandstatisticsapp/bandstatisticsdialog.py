from typing import Optional

from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph import PlotWidget
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from qgis.PyQt.QtGui import QMouseEvent, QColor
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QTableWidget, QComboBox, QCheckBox, \
    QLabel
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsRasterDataProvider, QgsRasterBandStats, \
    QgsRasterHistogram, QgsMapSettings, QgsRasterRenderer
from qgis.gui import QgsRasterBandComboBox, QgsMapLayerComboBox, QgsFilterLineEdit, QgsSpinBox, QgsMapCanvas
from typeguard import typechecked


@typechecked
class BandStatisticsDialog(QMainWindow):
    mLayer: QgsMapLayerComboBox
    mTable: QTableWidget

    mAddAllBands: QToolButton
    mAddRendererBands: QToolButton
    mAddBand: QToolButton
    mRemoveBand: QToolButton
    mDeleteAllBands: QToolButton

    mHistogramBinCount: QgsSpinBox
    mHistogramMinimum: QgsFilterLineEdit
    mHistogramMaximum: QgsFilterLineEdit
    mExtent: QComboBox
    mAccuracy: QComboBox

    mLiveUpdate: QCheckBox
    mApply: QToolButton

    EstimatedAccuracy, ActualAccuracy = 0, 1
    WholeRasterExtent, CurrentCanvasExtent = 0, 1

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mHistogramBinCount.setClearValue(self.mHistogramBinCount.value())
        self.mHistogramMinimum.clearValue()
        self.mHistogramMaximum.clearValue()

        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mHistogramBinCount.valueChanged.connect(self.onLiveUpdate)
        self.mHistogramMinimum.valueChanged.connect(self.onLiveUpdate)
        self.mHistogramMaximum.valueChanged.connect(self.onLiveUpdate)
        self.mExtent.currentIndexChanged.connect(self.onLiveUpdate)
        self.mAccuracy.currentIndexChanged.connect(self.onLiveUpdate)

        self.mAddBand.clicked.connect(self.onAddBandClicked)
        self.mAddRendererBands.clicked.connect(self.onAddRendererBandsClicked)
        self.mAddAllBands.clicked.connect(self.onAddAllBandsClicked)
        self.mRemoveBand.clicked.connect(self.onRemoveBandClicked)
        self.mDeleteAllBands.clicked.connect(self.onDeleteAllBandsClicked)

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

    def onLayerChanged(self):

        self.onDeleteAllBandsClicked()

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

    def onMapCanvasExtentsChanged(self):
        if self.mExtent.currentIndex() == self.WholeRasterExtent:
            return
        self.onLiveUpdate()

    def onAddRendererBandsClicked(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        renderer: QgsRasterRenderer = layer.renderer()
        for bandNo in renderer.usesBands():
            row = self.mTable.rowCount()
            self.onAddBandClicked()
            w: QgsRasterBandComboBox = self.mTable.cellWidget(row, 0)
            w.blockSignals(True)
            w.setBand(bandNo)
            w.blockSignals(False)

        self.onLiveUpdate()

    def onAddAllBandsClicked(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        for bandNo in range(1, layer.bandCount() + 1):
            row = self.mTable.rowCount()
            self.onAddBandClicked()
            w: QgsRasterBandComboBox = self.mTable.cellWidget(row, 0)
            w.blockSignals(True)
            w.setBand(bandNo)
            w.blockSignals(False)

        self.onLiveUpdate()

    def onRemoveBandClicked(self):
        row = self.mTable.currentRow()
        if row == -1:
            return
        self.mTable.removeRow(row)

    def onDeleteAllBandsClicked(self):
        for i in reversed(range(self.mTable.rowCount())):
            self.mTable.removeRow(i)

    def onAddBandClicked(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

        self.mTable.setRowCount(self.mTable.rowCount() + 1)
        row = self.mTable.rowCount() - 1
        w = QgsRasterBandComboBox()
        w.setLayer(layer)
        w.setBand(-1)
        w.bandChanged.connect(self.onLiveUpdate)
        self.mTable.setCellWidget(row, 0, w)

        for column in [2, 3, 4, 5]:
            self.mTable.setCellWidget(row, column, QLabel())

        w = HistogramPlotWidget()
        w.setFixedHeight(30)
        self.mTable.setCellWidget(row, 1, w)

        self.mTable.resizeColumnToContents(0)

    def onApplyClicked(self):
        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return
        provider: QgsRasterDataProvider = layer.dataProvider()
        extent = self.currentExtent()
        sampleSize = self.currentSampleSize()
        binCount = self.mHistogramBinCount.value()

        for row in range(self.mTable.rowCount()):
            w: QgsRasterBandComboBox = self.mTable.cellWidget(row, 0)
            bandNo = w.currentBand()
            if bandNo == -1:
                # clear and return
                for column in [2, 3, 4, 5]:
                    w: QLabel = self.mTable.cellWidget(row, column)
                    w.setText('')
                plotWidget: HistogramPlotWidget = self.mTable.cellWidget(row, 1)
                plotWidget.clear()
                continue

            # calculate stats
            stats: QgsRasterBandStats = provider.bandStatistics(bandNo, QgsRasterBandStats.All, extent, sampleSize)

            if self.mHistogramMinimum.isNull():
                minimum = stats.minimumValue
            else:
                try:
                    minimum = float(self.mHistogramMinimum.text())
                except Exception:
                    self.mHistogramMinimum.setText(stats.minimumValue)
                    minimum = stats.minimumValue

            if self.mHistogramMaximum.isNull():
                maximum = stats.maximumValue
            else:
                try:
                    maximum = float(self.mHistogramMaximum.text())
                except Exception:
                    self.mHistogramMaximum.setText(stats.maximumValue)
                    maximum = stats.maximumValue

            histogram: QgsRasterHistogram = provider.histogram(bandNo, binCount, minimum, maximum, extent, sampleSize)

            # set stats
            def smartRound(value: float) -> float:
                if abs(value) < 1:
                    return round(value, 4)
                elif abs(value) < 100:
                    return round(value, 2)
                else:
                    return round(value, 1)

            for column, value in enumerate([stats.minimumValue, stats.maximumValue, stats.mean, stats.stdDev], 2):
                w: QLabel = self.mTable.cellWidget(row, column)
                w.setText(str(smartRound(value)))

            # plot histogram
            plotWidget: HistogramPlotWidget = self.mTable.cellWidget(row, 1)
            plotWidget.clear()
            plotWidget.getAxis('bottom').setPen('#000000')
            plotWidget.getAxis('left').setPen('#000000')
            y = histogram.histogramVector
            x = range(binCount + 1)
            color = QColor(0, 153, 255)
            plot = plotWidget.plot(x, y, stepMode='center', fillLevel=0, brush=color)
            plot.setPen(color=color, width=1)
            plotWidget.autoRange()

    def onLiveUpdate(self):
        if not self.mLiveUpdate.isChecked():
            return

        self.onApplyClicked()


@typechecked
class HistogramPlotWidget(PlotWidget):
    def __init__(self):
        PlotWidget.__init__(self, parent=None, background='#ffffff')
        self.getPlotItem().hideAxis('bottom')
        self.getPlotItem().hideAxis('left')

    def mousePressEvent(self, ev):
        self.autoRange()

    def mouseMoveEvent(self, ev):
        self.autoRange()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.autoRange()
