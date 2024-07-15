from collections import defaultdict
from typing import Optional, List

import numpy as np
import plotly.graph_objects as go
from scipy.stats._crosstab import crosstab

from enmapbox.gui.widgets.multiplemaplayerselectionwidget.multiplemaplayerselectionwidget import \
    MultipleMapLayerSelectionWidget
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapbox.typeguard import typechecked
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QComboBox, QCheckBox
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRectangle, QgsPalettedRasterRenderer, QgsRasterLayer, QgsMapSettings
from qgis.gui import QgsDoubleSpinBox, QgsMapCanvas


@typechecked
class LandCoverChangeStatisticsDialog(QMainWindow):
    mLayers: MultipleMapLayerSelectionWidget
    mWebView: QWebView

    mExtent: QComboBox
    mAccuracy: QComboBox
    mClusterClasses: QCheckBox
    mMinimumClassSize: QgsDoubleSpinBox
    mShowClusteredClasses: QCheckBox
    mShowStableChanges: QCheckBox
    mShowNodePadding: QCheckBox
    mShowNodeNames: QCheckBox
    mShowColumnNames: QCheckBox

    mLiveUpdate: QCheckBox
    mApply: QToolButton

    EstimatedAccuracy, ActualAccuracy = 0, 1
    WholeRasterExtent, CurrentCanvasExtent = 0, 1
    LayerNameAnnotation, LayerSourceAnnotation = 0, 1

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.mLayers.setAllowRaster(True)
        self.mLayers.setAllowVector(False)
        self.mLayers.sigLayersChanged.connect(self.onLayersChanged)
        self.mExtent.currentIndexChanged.connect(self.onLiveUpdate)
        self.mAccuracy.currentIndexChanged.connect(self.onLiveUpdate)
        self.mClusterClasses.stateChanged.connect(self.onLiveUpdate)
        self.mMinimumClassSize.valueChanged.connect(self.onLiveUpdate)
        self.mShowClusteredClasses.stateChanged.connect(self.onLiveUpdate)
        self.mShowStableChanges.stateChanged.connect(self.onLiveUpdate)
        self.mShowNodePadding.stateChanged.connect(self.onLiveUpdate)
        self.mShowNodeNames.stateChanged.connect(self.onLiveUpdate)
        self.mShowColumnNames.stateChanged.connect(self.onLiveUpdate)

        self.mApply.clicked.connect(self.onApplyClicked)

        self.onApplyClicked()

    def currentLayer(self) -> Optional[QgsRasterLayer]:
        try:
            return self.mLayers.currentLayers()[0]
        except Exception:
            return None

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

    def onLayersChanged(self):

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

        self.onLiveUpdate()

    def onMapCanvasExtentsChanged(self):
        if self.mExtent.currentIndex() == self.WholeRasterExtent:
            return
        self.onLiveUpdate()

    def onApplyClicked(self):
        layers: List[QgsRasterLayer] = self.mLayers.currentLayers()
        if len(layers) < 2:
            self.mWebView.setHtml('select at least two land cover maps')
            return

        extent = self.currentExtent()
        sampleSize = self.currentSampleSize()
        if self.mClusterClasses.isChecked():
            minRelativeClassSize = self.mMinimumClassSize.value()
        else:
            minRelativeClassSize = 0.
        builder = LandCoverChangeSankeyPlotBuilder(layers)
        fig = builder.sankeyPlot(
            extent, sampleSize, minRelativeClassSize, self.mShowClusteredClasses.isChecked(),
            self.mShowStableChanges.isChecked(), self.mShowNodeNames.isChecked(), self.mShowColumnNames.isChecked(),
            self.mShowNodePadding.isChecked()
        )
        html = fig.to_html(include_plotlyjs='cdn')
        self.mWebView.setHtml(html)

    def onLiveUpdate(self):
        if not self.mLiveUpdate.isChecked():
            return

        self.onApplyClicked()


@typechecked
class LandCoverChangeSankeyPlotBuilder():

    def __init__(self, layers: List[QgsRasterLayer]):
        crsAuthid = layers[0].crs().authid()
        for layer in layers:
            assert layer.crs().authid() == crsAuthid, f'layer CRS not matching\n{layer.crs().authid()}\n{crsAuthid}'
            assert isinstance(layer.renderer(), QgsPalettedRasterRenderer)
        self.layers = layers

    def sankeyPlot(
            self, extent: QgsRectangle = None, sampleSize: int = None, minRelativeClassSize=0., showRestClass=True,
            showStableChanges=True, showNodeNames=True, showColumnNames=True, showNodePadding=True
    ):
        arrays = list()
        categoriess = list()
        restCategory = Category(-0.1, 'Rest', '#ff0000')
        for layer in self.layers:
            reader = RasterReader(layer)
            categories = Utils().categoriesFromRenderer(reader.layer.renderer(), reader.layer)
            width, height = reader.samplingWidthAndHeight(1, extent, sampleSize)
            array = np.array(reader.arrayFromBoundingBoxAndSize(extent, width, height, [1])[0], float)

            # Cluster small classes
            if minRelativeClassSize > 0:
                res = crosstab(array.flatten(), levels=[[c.value for c in categories]])
                relativeSizes = res.count / np.sum(res.count) * 100
                for c, p in zip(categories, relativeSizes):
                    if p < minRelativeClassSize:
                        array[array == c.value] = restCategory.value
                categories = [c for c, p in zip(categories, relativeSizes) if p >= minRelativeClassSize]
                if showRestClass:
                    categories.append(restCategory)

            arrays.append(array)
            categoriess.append(categories)

        nodes = defaultdict(list)
        for categories, layer in zip(categoriess, self.layers):
            for c in categories:
                if showNodeNames:
                    nodes['label'].append(c.name)
                else:
                    nodes['label'].append('')
                nodes['color'].append(c.color.upper())

        links = defaultdict(list)
        off1 = 0
        off2 = len(categoriess[0])
        for array1, array2, categories1, categories2 in zip(arrays, arrays[1:], categoriess, categoriess[1:]):
            levels = [[c.value for c in categories1], [c.value for c in categories2]]
            res = crosstab(array1.flatten(), array2.flatten(), levels=levels)
            count = res.count / np.sum(res.count) * 100

            for i1, l1 in enumerate(levels[0]):
                for i2, l2 in enumerate(levels[1]):
                    p = count[i1, i2]
                    color = categories2[i2].color.upper()
                    if not showStableChanges and categories1[i1].name == categories2[i2].name and p > 0:
                        links['source'].append(i1 + off1)
                        links['target'].append(i2 + off2)
                        links['value'].append(1e-10)
                        links['color'].append('rgba(0, 0, 0, 0)')
                    else:
                        links['source'].append(i1 + off1)
                        links['target'].append(i2 + off2)
                        links['value'].append(p)
                        links['color'].append(color)
            off1 += len(categories1)
            off2 += len(categories2)

        # Create the Sankey diagram
        if showNodePadding:
            pad = 15
        else:
            pad = 0
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=pad,  # Padding between nodes
                        thickness=20,  # Thickness of nodes
                        line=dict(color="black", width=0.5),
                        label=nodes["label"],
                        color=nodes["color"]
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
        if showColumnNames:
            for i, layer in enumerate(self.layers):
                annotations.append(dict(
                    x=i / (len(self.layers) - 1), y=1.01,
                    xanchor='center',
                    yanchor='bottom',
                    xref="paper", yref="paper",
                    showarrow=False,
                    text=layer.name(),
                    font=dict(size=12)
                ))

        # Update layout for better appearance
        fig.update_layout(
            # title_text="Land Cover Changes",
            annotations=annotations,
            font_size=16)

        return fig
