from typing import List

from enmapbox.gui.dataviews.docks import DockLabel, Dock
from enmapbox.gui.mapcanvas import MapCanvas, CanvasLink
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtCore import pyqtSignal, QSettings, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QToolButton, QMenu
from qgis.core import QgsCoordinateReferenceSystem, QgsLayerTree, QgsMapLayer, QgsLayerTreeLayer
from qgis.gui import QgsMapCanvas


class MapDockLabel(DockLabel):

    def __init__(self, *args, **kwds):
        super(MapDockLabel, self).__init__(*args, **kwds)

        self.addMapLink = QToolButton(self)
        self.addMapLink.setToolTip('Link with other map(s)')
        self.addMapLink.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_basic.svg'))
        self.mButtons.append(self.addMapLink)

        self.removeMapLink = QToolButton(self)
        self.removeMapLink.setToolTip('Remove links to this map')
        self.removeMapLink.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_open.svg'))
        self.mButtons.append(self.removeMapLink)


class MapDock(Dock):
    """
    A dock to visualize geodata that can be mapped
    """

    ISSUE_1344_REFERENCES: List[MapCanvas] = []

    sigLayersAdded = pyqtSignal(list)
    sigLayersRemoved = pyqtSignal(list)
    sigCrsChanged = pyqtSignal(QgsCoordinateReferenceSystem)
    sigRenderStateChanged = pyqtSignal()  # used by the progress bar

    def __init__(self, *args, **kwds):
        # initSrc = kwds.pop('initSrc', None)
        super(MapDock, self).__init__(*args, **kwds)
        self.mBaseName = self.title()

        from enmapbox.gui.mapcanvas import MapCanvas
        self.mCanvas: MapCanvas = MapCanvas()
        self.mCanvas.setWindowTitle(self.title())
        self.mCanvas.sigNameChanged.connect(self.setTitle)
        self.mCanvas.sigCrsChanged.connect(self.sigCrsChanged.emit)

        self.sigTitleChanged.connect(self.mCanvas.setWindowTitle)

        settings = QSettings()
        self.mCanvas.setCanvasColor(Qt.GlobalColor.black)
        self.mCanvas.enableAntiAliasing(settings.value('/qgis/enable_anti_aliasing', False, type=bool))
        self.layout.addWidget(self.mCanvas)

        # connect progress bar to render state
        self.mCanvas.renderStarting.connect(self.showProgressBar)
        self.mCanvas.renderComplete.connect(self.hideProgressBar)
        self.mCanvas.renderErrorOccurred.connect(self.hideProgressBar)

    def close(self):
        if isinstance(self.mCanvas, QgsMapCanvas):
            self.layout.takeAt(self.layout.indexOf(self.mCanvas))
            self.mCanvas.setVisible(False)
            self.mCanvas.setParent(None)
            if self.mCanvas not in self.ISSUE_1344_REFERENCES:
                self.ISSUE_1344_REFERENCES.append(self.mCanvas)
            if self.mCanvas in MapCanvas._instances:
                MapCanvas._instances.remove(self.mCanvas)

        super().close()

    def layerTree(self) -> QgsLayerTree:
        """
        Returns the layer tree that controls the MapCanvas layers.
        Can be none in case the MapCanvas is not linked to a layer tree
        :return: QgsLayerTree
        """
        return self.mapCanvas().layerTree()

    def showProgressBar(self):
        self.progressBar.setRange(0, 0)
        self.progressBar.show()

    def hideProgressBar(self):
        self.progressBar.hide()

    def treeNode(self) -> QgsLayerTree:
        return self.layerTree()

    def removeLayer(self, layer: QgsMapLayer):
        self.treeNode().removeLayer(layer)

    def mapCanvas(self) -> MapCanvas:
        return self.mCanvas

    def populateContextMenu(self, menu: QMenu):
        """
        Returns the MapDock context menu
        :return: QMenu
        """
        super(MapDock, self).populateContextMenu(menu)
        self.mCanvas.populateContextMenu(menu, None)
        return menu

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pass
        else:
            super(MapDock, self).mousePressEvent(event)

    def linkWithMapDock(self, mapDock: 'MapDock', linkType=CanvasLink.LINK_ON_CENTER_SCALE) -> CanvasLink:
        return self.linkWithCanvas(mapDock.mCanvas, linkType)

    def linkWithCanvas(self, canvas: QgsMapCanvas, linkType=CanvasLink.LINK_ON_CENTER_SCALE) -> CanvasLink:
        return self.mapCanvas().createCanvasLink(canvas, linkType)

    def addLayers(self, layers: List[QgsMapLayer]):
        tree: QgsLayerTree = self.layerTree()
        for lyr in layers:
            tree.addLayer(lyr)

    def insertLayer(self, idx, layerSource):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        from enmapbox.gui.dataviews.dockmanager import MapDockTreeNode

        enmapBox = EnMAPBox.instance()
        if enmapBox is not None:
            mapDockTreeNode: MapDockTreeNode
            for mapDockTreeNode in enmapBox.dockManagerTreeModel().mapDockTreeNodes():
                if mapDockTreeNode.dock is self:
                    mapDockTreeNode.insertLayer(idx=idx, layerSource=layerSource)

    def addOrUpdateLayer(self, layer: QgsMapLayer):
        """Add a new layer or update existing layer with matching name."""

        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox.instance()

        # look for existing layer and update ...
        layerNode: QgsLayerTreeLayer
        for index, layerNode in enumerate(self.treeNode().findLayers()):
            if layer.name() == layerNode.layer().name():
                if False and layer.dataProvider().name() == layerNode.layer().dataProvider().name():
                    Utils.setLayerDataSource(
                        layerNode.layer(), layer.dataProvider().name(), layer.source(), layer.extent()
                    )
                    layerNode.layer().setRenderer(layer.renderer().clone())
                    self.mapCanvas().refresh()
                    enmapBox.layerTreeView().refreshLayerSymbology(layerNode.layer().id())
                    return
                else:
                    # different providers can cause problems, so we better remove the existing and insert the new layer

                    # self.insertLayer(index, layer)  # currently broken, see issue #881

                    self.addLayers([layer])
                    self.removeLayer(layerNode.layer())

                    return

        # ... or add the layer
        self.addLayers([layer])
