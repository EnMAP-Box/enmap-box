from collections import defaultdict
from typing import Optional, List

import numpy as np
import plotly.graph_objects as go
from scipy.stats._crosstab import crosstab

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent, SpatialPoint
from enmapbox.typeguard import typechecked
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from landcoverchangestatisticsapp.enums import ExtentType, AccuracyType, AreaUnitsType
from landcoverchangestatisticsapp.landcoverchangestatisticsdatafilteringdockwidget import \
    LandCoverChangeStatisticsDataFilteringDockWidget
from landcoverchangestatisticsapp.landcoverchangestatisticssettingsdockwidget import \
    LandCoverChangeStatisticsSettingsDockWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtWidgets import QStatusBar
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QCheckBox
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRectangle, QgsPalettedRasterRenderer, QgsRasterLayer, QgsMapSettings, QgsUnitTypes
from qgis.gui import QgsMapCanvas


@typechecked
class LandCoverChangeStatisticsMainWindow(QMainWindow):
    mWebView: QWebView
    mStatusBar: QStatusBar

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()
        self.builder = LandCoverChangeSankeyPlotBuilder()

        # add status bar
        self.mLiveUpdate = QCheckBox('Live update')
        self.mLiveUpdate.setChecked(True)
        self.mApply = QToolButton()
        self.mApply.setText('Apply')
        self.mApply.clicked.connect(self.onApplyClicked)
        self.mStatusBar.addPermanentWidget(self.mLiveUpdate)
        self.mStatusBar.addPermanentWidget(self.mApply)

        # add dock widgets and toolbar buttons
        self.mDataFilteringDock = LandCoverChangeStatisticsDataFilteringDockWidget(parent=self)
        self.mDataFilteringDock.sigStateChanged.connect(self.onLiveUpdate)
        self.addDockWidget(Qt.RightDockWidgetArea, self.mDataFilteringDock)
        self.mSettingsDock = LandCoverChangeStatisticsSettingsDockWidget(parent=self)
        self.mSettingsDock.sigStateChanged.connect(self.onLiveUpdate)
        self.mSettingsDock.sigLayersChanged.connect(self.onLayersChanged)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.mSettingsDock)

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.enmapBox.sigCurrentLocationChanged.connect(self.onLiveUpdate)

        self.onApplyClicked()

    def currentLayers(self) -> List[QgsRasterLayer]:
        return self.mSettingsDock.mLayers.currentLayers()

    def currentExtent(self) -> Optional[SpatialExtent]:
        layers = self.currentLayers()
        if len(layers) == 0:
            return None

        grid = layers[0]
        if self.mSettingsDock.mExtent.currentIndex() == ExtentType.WholeRaster:
            return SpatialExtent(grid.crs(), grid.extent())
        elif self.mSettingsDock.mExtent.currentIndex() == ExtentType.CurrentCanvas:
            mapSettings: QgsMapSettings = self.mMapCanvas.mapSettings()
            return SpatialExtent(mapSettings.destinationCrs(), self.mMapCanvas.extent()).toCrs(grid.crs())
        else:
            raise ValueError()

    def currentSampleSize(self) -> int:
        if self.mSettingsDock.mAccuracy.currentIndex() == AccuracyType.Estimated:
            return int(QgsRasterLayer.SAMPLE_SIZE)
        elif self.mSettingsDock.mAccuracy.currentIndex() == AccuracyType.Actual:
            return 0  # use all pixel
        else:
            raise ValueError()

    def onLayersChanged(self):

        # disconnect old map canvas
        if self.mMapCanvas is not None:
            try:
                self.mMapCanvas.extentsChanged.disconnect(self.onMapCanvasExtentsChanged)
            except Exception:
                pass

        # connect new map canvas
        self.mMapCanvas = None
        layers = self.currentLayers()
        if len(layers) == 0:
            return
        grid = layers[0]
        for mapDock in self.enmapBox.dockManager().mapDocks():
            if grid in mapDock.mapCanvas().layers():
                self.mMapCanvas = mapDock.mapCanvas()
                break
        if self.mMapCanvas is not None:
            self.mMapCanvas.extentsChanged.connect(self.onMapCanvasExtentsChanged)

        try:
            self.builder.setGrid(grid)
            self.builder.setLayers(layers)
        except ValueError as error:
            self.mWebView.setHtml(str(error))
            self.mSettingsDock.mLayers.setCurrentLayers([])
            self.mDataFilteringDock.mTableClasses.setRowCount(0)
            self.mDataFilteringDock.mTableClasses.setColumnCount(0)
            self.onApplyClicked()
            return

        self.mDataFilteringDock.initGui(layers)

        self.onLiveUpdate()

    def onMapCanvasExtentsChanged(self):
        self.onLiveUpdate()

    def onApplyClicked(self):
        layers: List[QgsRasterLayer] = self.currentLayers()
        if len(layers) < 2:
            self.mWebView.setHtml('select at least two land cover maps')
            return

        extent = self.currentExtent()
        sampleSize = self.currentSampleSize()
        self.builder.setOptions(
            dict(
                showDiscardedClass=not self.mSettingsDock.mHideDiscardedClasses.isChecked(),
                rescaleSelectedClasses=self.mSettingsDock.mRescaleOtherClasses.isChecked(),
                showClassNames=self.mSettingsDock.mShowClassNames.isChecked(),
                showClassSizes=self.mSettingsDock.mShowClassSizes.isChecked(),
                classSizeUnits=self.mSettingsDock.mClassSizeUnits.currentIndex(),
                showLayerNames=self.mSettingsDock.mShowLayerNames.isChecked(),
                showNodePadding=self.mSettingsDock.mShowNodePadding.isChecked(),
                linkOpacity=self.mSettingsDock.mLinkOpacity.value()
            ))
        self.builder.readData(extent, sampleSize)
        self.mDataFilteringDock.setRelativeClassSizes(np.array(self.builder.categoryRelSizess).tolist())
        self.builder.setClassFilter(self.mDataFilteringDock.classFilter())
        fig = self.builder.sankeyPlot()
        html = fig.to_html(include_plotlyjs='cdn')
        self.mWebView.setHtml(html)

    def onLiveUpdate(self):
        if not self.mLiveUpdate.isChecked():
            return

        self.onApplyClicked()


@typechecked
class LandCoverChangeSankeyPlotBuilder():
    DiscardedCategory = Category(-0.1, 'Discarded', '#ff0000')

    def setGrid(self, grid: QgsRasterLayer):
        self.grid = grid

    def setLayers(self, layers: List[QgsRasterLayer]):
        crsAuthid = self.grid.crs().authid()
        for layer in layers:
            if layer.crs().authid() != crsAuthid:
                raise ValueError(f'layer CRS not matching:{layer.crs().authid()}, {crsAuthid}')
            if not isinstance(layer.renderer(), QgsPalettedRasterRenderer):
                raise ValueError(f'invalid layer style, use "Paletted/Unique values" renderer: {layer.name()}')
        if len(layers) < 2:
            raise ValueError('select at least two land cover maps')
        self.layers = layers
        self.currentExtent = None
        self.currentSampleSize = None
        self.currentLocation = None
        self.locationProfile = [None] * len(layers)

    def setClassFilter(self, filter: List[List[str]] = None):
        if filter is not None:
            assert len(filter) == len(self.layers)
        self.classFilter = filter

    def setOptions(self, options: dict):
        self.showDiscardedClass = options.get('showDiscardedClass', True)
        self.rescaleSelectedClasses = options.get('rescaleSelectedClasses', False)
        self.showClassNames = options.get('showClassNames', True)
        self.showClassSizes = options.get('showClassSizes', True)
        self.classSizeUnits = options.get('classSizeUnits', AreaUnitsType.Pixels)
        self.showLayerNames = options.get('showLayerNames', True)
        self.showNodePadding = options.get('showNodePadding', True)
        self.linkOpacity = options.get('linkOpacity', 75)
        self.title = options.get('title', None)

    def readData(self, extent: QgsRectangle, sampleSize: int):
        if extent == self.currentExtent and sampleSize == self.currentSampleSize:
            return  # only read data if necessary
        self.currentExtent = extent
        self.currentSampleSize = sampleSize

        self.categoriess = list()
        self.categorySizess = list()
        self.categoryRelSizess = list()
        self.linkSizess = list()

        width, height = RasterReader(self.grid).samplingWidthAndHeight(1, extent, sampleSize)

        def readLayer(layer):
            reader = RasterReader(layer)
            array = np.array(reader.arrayFromBoundingBoxAndSize(extent, width, height, [1])[0], float)
            categories = Utils().categoriesFromRenderer(reader.layer.renderer(), reader.layer)
            categorySizes = crosstab(array.flatten(), levels=[[c.value for c in categories]]).count
            categoryRelSizes = categorySizes / np.sum(categorySizes)
            return array, categories, categorySizes, categoryRelSizes

        for i, (layer, nextLayer) in enumerate(zip(self.layers, self.layers[1:])):
            if i == 0:
                array, categories, categorySizes, categoryRelSizes = readLayer(layer)
            else:
                array, categories, categorySizes, categoryRelSizes = array2, categories2, categorySizes2, \
                                                                     categoryRelSizes2
            array2, categories2, categorySizes2, categoryRelSizes2 = readLayer(nextLayer)

            levels = [[c.value for c in categories], [c.value for c in categories2]]
            linkSizes = crosstab(array.flatten(), array2.flatten(), levels=levels).count
            self.linkSizess.append(linkSizes)
            self.categoriess.append(categories)
            self.categorySizess.append(categorySizes)
            self.categoryRelSizess.append(categoryRelSizes)
        self.categoriess.append(categories2)
        self.categorySizess.append(categorySizes2)
        self.categoryRelSizess.append(categoryRelSizes2)

    def readLocationData(self, location: SpatialPoint):
        if location == self.currentLocation:
            return

        self.locationProfile = list()
        for layer in self.layers:
            reader = RasterReader(layer)
            pixel = reader.pixelByPoint(location)
            self.locationProfile.append(
                float(reader.arrayFromPixelOffsetAndSize(pixel.x(), pixel.y(), 1, 1, [1])[0][0, 0])
            )

    @classmethod
    def recodeConfusionMatrix(
            cls, matrix: np.ndarray, categories1: List[Category], categories2: List[Category], filter1: List[str],
            filter2: List[str]
    ):
        assert matrix.shape == (len(categories1), len(categories2))
        newCategories1 = [c for c in categories1 if c.name in filter1]
        newCategories2 = [c for c in categories2 if c.name in filter2]
        newMatrix = np.zeros((len(newCategories1) + 1, len(newCategories2) + 1), matrix.dtype)
        for i1, c1 in enumerate(categories1):
            for i2, c2 in enumerate(categories2):
                try:
                    new1 = newCategories1.index(c1)  # passes the filter
                except ValueError:
                    new1 = -1  # assigned to rest
                try:
                    new2 = newCategories2.index(c2)  # passes the filter
                except ValueError:
                    new2 = -1  # assigned to rest
                newMatrix[new1, new2] += matrix[i1, i2]

        return newMatrix, newCategories1 + [cls.DiscardedCategory], newCategories2 + [cls.DiscardedCategory]

    @classmethod
    def recodeClassSizes(cls, values: np.ndarray, categories: List[Category], filter: List[str]):
        newCategories = [c for c in categories if c.name in filter] + [cls.DiscardedCategory]
        newValues = np.zeros((len(newCategories),), values.dtype)
        for i, c in enumerate(categories):
            try:
                new = newCategories.index(c)  # passes the filter
            except ValueError:
                new = -1  # assigned to Discarded
            newValues[new] += values[i]
        return newValues, newCategories

    def estimateClassArea(self, countSampled: int, fraction: float):
        width, height = RasterReader(self.grid).samplingWidthAndHeight(1, self.currentExtent, 0)
        widthSampled, heightSampled = RasterReader(self.grid).samplingWidthAndHeight(
            1, self.currentExtent, self.currentSampleSize
        )
        n = width * height
        nSampled = widthSampled * heightSampled
        count = countSampled / nSampled * n

        fromUnit: QgsUnitTypes.AreaUnit = QgsUnitTypes.distanceToAreaUnit(self.grid.crs().mapUnits())
        factorToSquareMeters = QgsUnitTypes.fromUnitToUnitFactor(fromUnit, QgsUnitTypes.AreaSquareMeters)
        factorToHectares = QgsUnitTypes.fromUnitToUnitFactor(fromUnit, QgsUnitTypes.AreaHectares)
        factorToSquareKilometers = QgsUnitTypes.fromUnitToUnitFactor(fromUnit, QgsUnitTypes.AreaSquareKilometers)

        pixelSize = self.grid.rasterUnitsPerPixelX() * self.grid.rasterUnitsPerPixelY()

        def smartRound(value: float) -> float:
            if abs(value) < 1:
                return round(value, 4)
            elif abs(value) < 10:
                return round(value, 3)
            elif abs(value) < 100:
                return round(value, 2)
            elif abs(value) < 1000:
                return round(value, 1)
            else:
                return round(value)

        area = {
            AreaUnitsType.Percentages: smartRound(fraction * 100),
            AreaUnitsType.Pixels: int(round(count)),
            AreaUnitsType.SquareMeters: smartRound(count * pixelSize * factorToSquareMeters),
            AreaUnitsType.Hectares: smartRound(count * pixelSize * factorToHectares),
            AreaUnitsType.SquareKilometers: smartRound(count * pixelSize * factorToSquareKilometers)
        }

        return area

    def applyClassFilter(self):

        if self.classFilter is None:
            return self.categoriess, self.linkSizess, self.categorySizess, self.categoryRelSizess

        assert len(self.classFilter) == len(self.categoriess)

        categoriess = list()
        linkSizess = list()
        for i, matrix in enumerate(self.linkSizess):
            linkSizes, categories1, categories2 = self.recodeConfusionMatrix(
                matrix, self.categoriess[i], self.categoriess[i + 1], self.classFilter[i], self.classFilter[i + 1]
            )
            linkSizess.append(linkSizes)
            categoriess.append(categories1)
        categoriess.append(categories2)

        categorySizess = [self.recodeClassSizes(values, self.categoriess[i], self.classFilter[i])
                          for i, values in enumerate(self.categorySizess)]
        categoryRelSizess = [self.recodeClassSizes(values, self.categoriess[i], self.classFilter[i])
                             for i, values in enumerate(self.categoryRelSizess)]
        return categoriess, linkSizess, categorySizess, categoryRelSizess

    def sankeyPlot(self):

        # apply class filter
        categoriess, linkSizess, categorySizess, categoryRelSizess = self.applyClassFilter()

        # estimate areas
        areass = list()
        for i, (categorySizes, categoryRelSizes) in enumerate(zip(categorySizess, categoryRelSizess)):
            areas = [self.estimateClassArea(int(n), float(nrel))
                     for n, nrel in zip(categorySizes[0], categoryRelSizes[0])]

            areass.append(areas)

        nodes = defaultdict(list)
        for i1, (categories, layer, relativeSizes) in enumerate(zip(categoriess, self.layers, categoryRelSizess)):
            for i2, (c, n) in enumerate(zip(categories, relativeSizes[0])):
                color = c.color
                label = ''
                if self.showClassNames:
                    label += c.name
                if self.showClassSizes:
                    areas = areass[i1][i2]
                    value = areas[self.classSizeUnits]
                    unit = ['%', 'px', 'm²', 'ha', 'km²'][self.classSizeUnits]
                    if self.showClassNames:
                        label += f' ({value} {unit})'
                    else:
                        label += f'{value} {unit}'
                if not self.showDiscardedClass and c == self.DiscardedCategory:
                    color = 'rgba(0, 0, 0, 0)'
                    label = ''

                nodes['label'].append(label)
                nodes['color'].append(color)

        def makeRgba(color: QColor) -> str:
            return f'rgba({color.red()},{color.green()},{color.blue()},{self.linkOpacity / 100})'

        links = defaultdict(list)
        off1 = 0
        off2 = len(categoriess[0])
        for linkSizes, categories1, categories2, locationValue1, locationValue2 in zip(
                linkSizess, categoriess, categoriess[1:], self.locationProfile, self.locationProfile[1:]
        ):
            levels = [[c.value for c in categories1], [c.value for c in categories2]]
            count = linkSizes / np.sum(linkSizes) * 100

            for i1, l1 in enumerate(levels[0]):
                for i2, l2 in enumerate(levels[1]):

                    p = count[i1, i2]
                    color = makeRgba(QColor(categories2[i2].color))

                    # mRescaleSelectedClasses

                    if l1 == self.DiscardedCategory.value or l2 == self.DiscardedCategory.value:
                        if not self.showDiscardedClass:
                            if self.rescaleSelectedClasses:
                                continue
                            color = 'rgba(0, 0, 0, 0)'

                    if 0:  # not showStableChanges and categories1[i1].name == categories2[i2].name and p > 0:
                        links['source'].append(i1 + off1)
                        links['target'].append(i2 + off2)
                        links['value'].append(1e-10)
                        links['color'].append('rgba(0, 0, 0, 0)')
                    else:
                        links['source'].append(i1 + off1)
                        links['target'].append(i2 + off2)
                        links['value'].append(p)
                        if locationValue1 == l1 and locationValue2 == l2:
                            links['color'].append(makeRgba(highlightColor))
                        else:
                            links['color'].append(color)
            off1 += len(categories1)
            off2 += len(categories2)

        # Create the Sankey diagram
        if self.showNodePadding:
            pad = 15
        else:
            pad = 0
        fig = go.Figure(
            data=[
                go.Sankey(
                    arrangement='perpendicular',
                    node=dict(
                        pad=pad,  # Padding between nodes
                        thickness=20,  # Thickness of nodes
                        line=dict(color='black', width=0.),
                        label=nodes["label"],
                        color=nodes["color"],
                    ),
                    link=dict(
                        source=links["source"],  # Indices of source nodes
                        target=links["target"],  # Indices of target nodes
                        value=links["value"],  # Values of the links
                        color=links["color"]  # Colors for the links
                    )
                )
            ]
        )
        # Create annotations
        annotations = []
        if self.showLayerNames:
            for i, layer in enumerate(self.layers):
                if i == 0:
                    xanchor = 'left'
                elif i == len(self.layers) - 1:
                    xanchor = 'right'
                else:
                    xanchor = 'center'
                annotations.append(dict(
                    x=i / (len(self.layers) - 1), y=1.01,
                    xanchor=xanchor,
                    yanchor='bottom',
                    xref="paper", yref="paper",
                    showarrow=False,
                    text=layer.name(),
                    font=dict(size=12)
                ))

        # Update layout for better appearance
        fig.update_layout(
            title_text=self.title,
            annotations=annotations,
            font_size=16)

        return fig
