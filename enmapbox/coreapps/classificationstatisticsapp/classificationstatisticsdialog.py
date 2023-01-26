from math import ceil, sqrt
from typing import Optional, List

import numpy as np
from qgis.PyQt.QtCore import Qt, QRectF
from qgis.PyQt.QtGui import QMouseEvent, QColor, QPicture, QPainter
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QTableWidget, QComboBox, QCheckBox, \
    QTableWidgetItem
from qgis.PyQt.uic import loadUi
from osgeo import gdal
from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsMapSettings, QgsPalettedRasterRenderer, QgsProject, \
    QgsRasterRange, QgsRectangle, QgsFeature, QgsCoordinateTransform, \
    QgsVectorLayer, QgsVectorFileWriter, QgsUnitTypes
from qgis.gui import QgsMapLayerComboBox, QgsMapCanvas, QgsFieldComboBox, QgsFeaturePickerWidget

from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph import PlotWidget, GraphicsObject, mkBrush, mkPen
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from typeguard import typechecked


@typechecked
class ClassificationStatisticsDialog(QMainWindow):
    mLayer: QgsMapLayerComboBox
    mTable: QTableWidget

    mAreaUnits: QComboBox
    mOrder: QComboBox
    mExtent: QComboBox
    mAccuracy: QComboBox
    mRoiLayer: QgsMapLayerComboBox
    mRoiField: QgsFieldComboBox
    mRoiFeature: QgsFeaturePickerWidget

    mLiveUpdate: QCheckBox
    mApply: QToolButton

    SquareMeters, Hectares, SquareKilometers = 0, 1, 2
    (
        DefaultOrder, ValueAscendingOrder, ValueDescendingOrder, LabelAscendingOrder, LabelDescendingOrder,
        SizeAscendingOrder, SizeDescendingOrder
    ) = 0, 1, 2, 3, 4, 5, 6
    EstimatedAccuracy, ActualAccuracy = 0, 1
    WholeRasterExtent, CurrentCanvasExtent = 0, 1

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        exceptedLayers = [layer for layer in QgsProject.instance().mapLayers().values()
                          if not isinstance(layer.renderer(), QgsPalettedRasterRenderer)]
        self.mLayer.setExceptedLayerList(exceptedLayers)
        self.mTable.horizontalHeader().setSectionsMovable(True)
        self.mRoiLayer.setFilters(QgsMapLayerProxyModel.VectorLayer)

        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mAreaUnits.currentIndexChanged.connect(self.onLiveUpdate)
        self.mOrder.currentIndexChanged.connect(self.onLiveUpdate)
        self.mExtent.currentIndexChanged.connect(self.onLiveUpdate)
        self.mAccuracy.currentIndexChanged.connect(self.onLiveUpdate)
        self.mRoiLayer.layerChanged.connect(self.mRoiFeature.setLayer)
        self.mRoiLayer.layerChanged.connect(self.mRoiField.setLayer)
        self.mRoiField.fieldChanged.connect(self.mRoiFeature.setDisplayExpression)
        self.mRoiFeature.featureChanged.connect(self.onLiveUpdate)

        self.mApply.clicked.connect(self.onApplyClicked)

    def currentLayer(self) -> Optional[QgsRasterLayer]:
        return self.mLayer.currentLayer()

    def currentCategories(self) -> Optional[List[Category]]:
        layer = self.currentLayer()
        if layer is None or not isinstance(layer.renderer(), QgsPalettedRasterRenderer):
            return None

        categories = Utils.categoriesFromPalettedRasterRenderer(layer.renderer())
        return categories

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

        self.mTable.setRowCount(0)

        layer = self.currentLayer()
        if layer is None:
            return

        categories = self.currentCategories()
        if categories is None:
            self.mLayer.setLayer(None)
            return

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

        # add new categories
        self.mTable.setRowCount(len(categories))
        for row, category in enumerate(categories):
            w = QCheckBox('')
            w.setCheckState(Qt.Checked)
            w.setDisabled(True)
            w.toggled.connect(self.onCategoryToogled)
            self.mTable.setCellWidget(row, 0, w)
            self.mTable.setItem(row, 1, QTableWidgetItem(''))
            self.mTable.setCellWidget(row, 2, HistogramPlotWidget())
            self.mTable.setItem(row, 3, QTableWidgetItem(''))
            self.mTable.setItem(row, 4, QTableWidgetItem(''))
            self.mTable.setItem(row, 5, QTableWidgetItem(''))

        self.onLiveUpdate()

    def onMapCanvasExtentsChanged(self):
        if self.mExtent.currentIndex() == self.WholeRasterExtent:
            return
        self.onLiveUpdate()

    def onCategoryToogled(self):
        layer = self.currentLayer()
        reader = RasterReader(layer)
        renderer: QgsPalettedRasterRenderer = layer.renderer()
        bandNo = renderer.band()

        self.currentCategories()
        categories = self.currentCategories()

        userNoDataValues = list()
        for row, category in enumerate(categories):
            checkBox: QCheckBox = self.mTable.cellWidget(row, 0)
            if not checkBox.isChecked():
                categoryValue = float(checkBox.text())
                userNoDataValues.append(QgsRasterRange(categoryValue, categoryValue))
        reader.setUserNoDataValue(bandNo, userNoDataValues)
        layer.triggerRepaint()

        self.onApplyClicked()

    def onApplyClicked(self):

        if self.isHidden():
            return

        layer = self.currentLayer()
        if layer is None:
            return

        categories = self.currentCategories()
        if categories is None:
            return

        renderer: QgsPalettedRasterRenderer = layer.renderer()

        # derive sampling extent and size
        reader = RasterReader(layer)
        bandNo = renderer.band()
        extent = self.currentExtent()
        extent = extent.intersect(reader.extent())

        # derive size
        width = extent.width() / reader.rasterUnitsPerPixelX()
        height = extent.height() / reader.rasterUnitsPerPixelY()
        actualPixelCount = width * height

        width = max(min(int(round(width)), reader.width()), 1)  # 1 <= width <= layerWidth
        height = max(min(int(round(height)), reader.height()), 1)  # 1 <= height <= layerHeight

        sampleSize = self.currentSampleSize()
        if sampleSize != 0:
            sampleFraction = sqrt(min(sampleSize / (width * height), 1))
            width = ceil(width * sampleFraction)
            height = ceil(height * sampleFraction)
        else:
            sampleFraction = 1.

        # improve sample fraction estimate
        estimatedPixelCount = float(width) * float(height)
        sampleFraction = estimatedPixelCount / actualPixelCount

        # read data
        array = reader.arrayFromBoundingBoxAndSize(extent, width, height, bandList=[bandNo])[0]

        # create ROI mask and subset data
        marray = self.createRoiMaskArray(extent, width, height)
        if marray is not None:
            array = array[marray]

        # calculate unique value counts
        uniqueValues, uniqueCounts = map(list, np.unique(array, return_counts=True))

        # calculate stats
        counts = list()
        for category in categories:
            if category.value in uniqueValues:
                count = uniqueCounts[uniqueValues.index(category.value)]
                count = int(round(count / sampleFraction))
            else:
                count = 0
            counts.append(count)

        n = sum(counts)
        if n != 0:
            fractions = [count / n for count in counts]
        else:
            fractions = [0] * len(counts)

        fromUnit: QgsUnitTypes.AreaUnit = QgsUnitTypes.distanceToAreaUnit(layer.crs().mapUnits())
        if self.mAreaUnits.currentIndex() == self.SquareMeters:
            toUnit = QgsUnitTypes.AreaSquareMeters
        elif self.mAreaUnits.currentIndex() == self.Hectares:
            toUnit = QgsUnitTypes.AreaHectares
        elif self.mAreaUnits.currentIndex() == self.SquareKilometers:
            toUnit = QgsUnitTypes.AreaSquareKilometers
        else:
            raise ValueError()
        if fromUnit in [QgsUnitTypes.AreaUnknownUnit, QgsUnitTypes.AreaSquareDegrees]:
            areas = [None] * len(counts)
        else:
            factor = QgsUnitTypes.fromUnitToUnitFactor(fromUnit, toUnit)
            areas = [count * layer.rasterUnitsPerPixelX() * layer.rasterUnitsPerPixelY() * factor
                     for count in counts]

        # sort data
        if self.mOrder.currentIndex() == self.DefaultOrder:
            by, reverse = list(range(len(categories))), False
        elif self.mOrder.currentIndex() == self.ValueAscendingOrder:
            by, reverse = [category.value for category in categories], False
        elif self.mOrder.currentIndex() == self.ValueDescendingOrder:
            by, reverse = [category.value for category in categories], True
        elif self.mOrder.currentIndex() == self.LabelAscendingOrder:
            by, reverse = [category.name for category in categories], False
        elif self.mOrder.currentIndex() == self.LabelDescendingOrder:
            by, reverse = [category.name for category in categories], True
        elif self.mOrder.currentIndex() == self.SizeAscendingOrder:
            by, reverse = counts, False
        elif self.mOrder.currentIndex() == self.SizeDescendingOrder:
            by, reverse = counts, True
        else:
            raise ValueError()
        categories, counts, fractions, areas = Utils.sortedBy([categories, counts, fractions, areas], by, reverse)

        # update table
        for row, (category, count, fraction, area) in enumerate(zip(categories, counts, fractions, areas)):

            checkBox: QCheckBox = self.mTable.cellWidget(row, 0)
            checkBox.blockSignals(True)
            checkBox.setEnabled(True)
            checkBox.setText(str(category.value))
            checkBox.setChecked(not reader.provider.userNoDataValuesContains(bandNo, category.value))
            checkBox.blockSignals(False)

            self.mTable.item(row, 1).setText(category.name)

            if not checkBox.isChecked():
                # clear and return
                plotWidget: HistogramPlotWidget = self.mTable.cellWidget(row, 2)
                plotWidget.clear()
                for column in [3, 4, 5]:
                    self.mTable.item(row, column).setText('')
                continue

            # plot histogram
            plotWidget: HistogramPlotWidget = self.mTable.cellWidget(row, 2)
            plotWidget.clear()
            plotWidget.getAxis('bottom').setPen('#000000')
            plotWidget.getAxis('left').setPen('#000000')
            rectItem = RectItem(QRectF(0, 0, fraction, 1), QColor(category.color))
            plotWidget.addItem(rectItem)
            plotWidget.setRange(QRectF(0, 0, 1, 1))

            self.mTable.item(row, 3).setText(str(round(fraction * 100., 2)))
            self.mTable.item(row, 4).setText(str(count))
            if area is None:
                self.mTable.item(row, 5).setText('')
            else:
                self.mTable.item(row, 5).setText(str(round(area, 2)))

    def onLiveUpdate(self):
        if not self.mLiveUpdate.isChecked():
            return

        self.onApplyClicked()

    def createRoiMaskArray(self, extent: QgsRectangle, width: int, height: int) -> Optional[np.ndarray]:

        roiLayer: QgsVectorLayer = self.mRoiLayer.currentLayer()
        if roiLayer is None:
            return None

        feature: QgsFeature = self.mRoiFeature.feature()
        if feature is None:
            return None

        roiLayer.removeSelection()
        roiLayer.select(feature.id())

        layer = self.currentLayer()

        filename = '/vsimem/ClassificationStatistics/roi.gpkg'
        transformContext = QgsProject.instance().transformContext()
        saveVectorOptions = QgsVectorFileWriter.SaveVectorOptions()
        saveVectorOptions.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        saveVectorOptions.ct = QgsCoordinateTransform(roiLayer.crs(), layer.crs(), QgsProject.instance())
        saveVectorOptions.onlySelectedFeatures = True
        saveVectorOptions.skipAttributeCreation = True
        saveVectorOptions.layerName = 'ROI'
        error, message, newFilename, newLayer = QgsVectorFileWriter.writeAsVectorFormatV3(
            roiLayer, filename, transformContext, saveVectorOptions
        )
        if not error == QgsVectorFileWriter.NoError:
            raise RuntimeError(f'Fail error {error}:{message}')

        options = gdal.RasterizeOptions(
            # format='MEM',
            outputType=gdal.GDT_Byte,
            creationOptions=EnMAPProcessingAlgorithm.DefaultGTiffCreationOptions,
            initValues=0,
            outputBounds=[extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()],
            width=width, height=height
        )
        filename2 = '/vsimem/ClassificationStatistics/roi.tif'
        ds: gdal.Dataset = gdal.Rasterize(filename2, filename, options=options)

        marray = ds.ReadAsArray()
        assert marray.shape == (height, width)
        return marray.astype(bool)


@typechecked
class HistogramPlotWidget(PlotWidget):
    def __init__(self):
        PlotWidget.__init__(self, parent=None, background='#ffffff')
        self.getPlotItem().hideAxis('bottom')
        self.getPlotItem().hideAxis('left')
        self.setFixedHeight(30)

    def mousePressEvent(self, ev):
        self.autoRange()

    def mouseMoveEvent(self, ev):
        self.autoRange()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.autoRange()


class RectItem(GraphicsObject):
    # adopted from https://stackoverflow.com/questions/60012070/drawing-a-rectangle-in-pyqtgraph
    def __init__(self, rect: QRectF, color: QColor, parent=None):
        super().__init__(parent)
        self._rect = rect
        self._color = color
        self.picture = QPicture()
        self._generate_picture()

    @property
    def rect(self):
        return self._rect

    def _generate_picture(self):
        painter = QPainter(self.picture)
        painter.setPen(mkPen(self._color))
        painter.setBrush(mkBrush(self._color))
        painter.drawRect(self.rect)
        painter.end()

    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QRectF(self.picture.boundingRect())
