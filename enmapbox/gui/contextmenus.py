from qgis.PyQt.QtCore import QPointF
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication, QWidgetAction

from enmapbox import messageLog
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMenu
from typing import List, Iterator, Tuple

from qgis.core import QgsVectorLayer, QgsLayerTree, QgsRasterLayer, QgsProject, QgsMapLayerProxyModel, Qgis

from qgis.gui import QgsMapLayerComboBox, QgisInterface
from qgis.core import QgsMapLayer, QgsPointXY

from enmapbox.gui.datasources.datasources import DataSource
from enmapbox.gui.dataviews.docks import Dock
from enmapbox.gui.mapcanvas import MapCanvas, CanvasLink
from qps.crosshair.crosshair import CrosshairDialog
from qps.utils import qgisAppQgisInterface, SpatialPoint, SpatialExtent


class EnMAPBoxAbstractContextMenuProvider(QObject):

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def enmapBox(self) -> 'EnMAPBox':
        from enmapbox.gui.enmapboxgui import EnMAPBox
        return EnMAPBox.instance()

    def populateMapLayerMenu(self, menu: QMenu, mapLayer: QgsMapLayer):
        """
        Overwrite to extend the map layer menu
        """
        pass

    def populateMapCanvasMenu(self, menu: QMenu, mapCanvas: MapCanvas, pos: QPointF, point: QgsPointXY):
        """
        Overwrite to extend the MapCanvas menu
        """
        pass

    def populateDataSourceMenu(self, menu: QMenu, dataSource: DataSource):
        """
        Overwrite to extend a DataSource menu
        """
        pass

    def populateDataViewMenu(self, menu: QMenu, dataView: Dock):
        """
        Overwrite to extend a DataView (aka EnMAP-Box Dock) menu
        """
        pass


class EnMAPBoxContextMenuProvider(EnMAPBoxAbstractContextMenuProvider):
    """
    Core context menu provider
    """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def populateMapCanvasMenu(self, menu: QMenu, mapCanvas: MapCanvas, pos: QPointF, point: QgsPointXY):

        action = menu.addAction('Link with other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_basic.svg'))
        action.triggered.connect(lambda: CanvasLink.ShowMapLinkTargets(self))
        action = menu.addAction('Remove links to other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_open.svg'))
        action.triggered.connect(lambda: self.removeAllCanvasLinks())

        qgisApp = qgisAppQgisInterface()
        b = isinstance(qgisApp, QgisInterface)
        menu.addSeparator()
        m = menu.addMenu('QGIS...')
        m.setIcon(QIcon(r':/images/themes/default/providerQgis.svg'))
        action = m.addAction('Use map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: self.setCenter(SpatialPoint.fromMapCanvasCenter(qgisApp.mapCanvas())))

        action = m.addAction('Set map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: qgisApp.mapCanvas().setCenter(
                self.spatialCenter().toCrs(qgisApp.mapCanvas().mapSettings().destinationCrs())))

        action = m.addAction('Use map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: self.setExtent(SpatialExtent.fromMapCanvas(qgisApp.mapCanvas())))

        action = m.addAction('Set map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: qgisApp.mapCanvas().setExtent(
                self.spatialExtent().toCrs(qgisApp.mapCanvas().mapSettings().destinationCrs())))

        menu.addSeparator()
        m = menu.addMenu('Crosshair')

        if self.crosshairIsVisible():
            action = m.addAction('Hide')
            action.triggered.connect(lambda: self.setCrosshairVisibility(False))
        else:
            action = m.addAction('Show')
            action.triggered.connect(lambda: self.setCrosshairVisibility(True))

        action = m.addAction('Style')
        action.triggered.connect(lambda: self.setCrosshairStyle(
            CrosshairDialog.getCrosshairStyle(
                crosshairStyle=self.crosshairStyle(), mapCanvas=self
            )
        ))

        mPxGrid = m.addMenu('Pixel Grid')
        if self.mCrosshairItem.crosshairStyle().mShowPixelBorder:
            action = mPxGrid.addAction('Hide')
            action.triggered.connect(lambda: self.mCrosshairItem.crosshairStyle().setShowPixelBorder(False))

        mPxGrid.addSeparator()

        rasterLayers = [lyr for lyr in self.layers() if isinstance(lyr, QgsRasterLayer) and lyr.isValid()]

        def onShowRasterGrid(layer: QgsRasterLayer):
            self.mCrosshairItem.setVisibility(True)
            self.mCrosshairItem.crosshairStyle().setShowPixelBorder(True)
            self.mCrosshairItem.setRasterGridLayer(layer)

        actionTop = mPxGrid.addAction('Top Raster')
        actionBottom = mPxGrid.addAction('Bottom Raster')

        if len(rasterLayers) == 0:
            actionTop.setEnabled(False)
            actionBottom.setEnabled(False)
        else:
            actionTop.triggered.connect(lambda b, layer=rasterLayers[0]: onShowRasterGrid(layer))
            actionBottom.triggered.connect(lambda b, layer=rasterLayers[-1]: onShowRasterGrid(layer))

        mPxGrid.addSeparator()
        wa = QWidgetAction(mPxGrid)

        cb = QgsMapLayerComboBox()
        cb.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb.setAllowEmptyLayer(True)

        # keep the list short an focus on

        # list each source only once
        all_layers = QgsProject.instance().mapLayers().values()
        all_layers = sorted(all_layers, key=lambda l: not l.title().startswith('[EnMAP-Box]'))

        excepted_layers = []
        sources = []
        for lyr in all_layers:
            if lyr.source() in sources:
                excepted_layers.append(lyr)
            else:
                sources.append(lyr.source())
        cb.setExceptedLayerList(excepted_layers)

        for i in range(cb.count()):
            lyr = cb.layer(i)
            if lyr == self.mCrosshairItem.rasterGridLayer():
                cb.setCurrentIndex(i)
                break
        cb.layerChanged.connect(onShowRasterGrid)
        wa.setDefaultWidget(cb)
        mPxGrid.addAction(wa)

        # action.triggered.connect(lambda b, layer=l: onShowRasterGrid(layer))

        menu.addSeparator()

        action = menu.addAction('Zoom Full')
        action.setIcon(QIcon(':/images/themes/default/mActionZoomFullExtent.svg'))
        action.triggered.connect(self.zoomToFullExtent)

        action = menu.addAction('Zoom Native Resolution')
        action.setIcon(QIcon(':/images/themes/default/mActionZoomActual.svg'))
        action.setEnabled(any([lyr for lyr in self.layers() if isinstance(lyr, QgsRasterLayer)]))
        action.triggered.connect(lambda: self.zoomToPixelScale(spatialPoint=point))

        menu.addSeparator()

        m = menu.addMenu('Save to...')
        action = m.addAction('PNG')
        action.triggered.connect(lambda: self.saveMapImageDialog('PNG'))
        action = m.addAction('JPEG')
        action.triggered.connect(lambda: self.saveMapImageDialog('JPG'))
        action = m.addAction('Clipboard')
        action.triggered.connect(lambda: QApplication.clipboard().setPixmap(self.pixmap()))
        action = menu.addAction('Copy layer paths')
        action.triggered.connect(lambda: QApplication.clipboard().setText('\n'.join(self.layerPaths())))

        menu.addSeparator()

        action = menu.addAction('Refresh')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda: mapCanvas.refresh())

        action = menu.addAction('Refresh all layers')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda: mapCanvas.refreshAllLayers())

        action = menu.addAction('Clear')
        action.triggered.connect(mapCanvas.clearLayers)

        menu.addSeparator()
        action = menu.addAction('Set CRS...')
        action.triggered.connect(mapCanvas.setCRSfromDialog)

        action = menu.addAction('Set background color')
        action.triggered.connect(mapCanvas.setBackgroundColorFromDialog)

        action = menu.addAction('Show background layer')
        action.triggered.connect(mapCanvas.setBackgroundLayer)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = self.enmapBox()
        node = self.layerTree()
        if isinstance(emb, EnMAPBox) and isinstance(node, QgsLayerTree):

            slws = emb.spectralLibraryWidgets()
            if len(slws) > 0:
                m = menu.addMenu('Add Spectral Library')
                for slw in slws:
                    speclib = slw.speclib()
                    if isinstance(speclib, QgsVectorLayer):
                        a = m.addAction(speclib.name())
                        a.setToolTip(speclib.source())
                        a.triggered.connect(lambda *args, sl=speclib, n=node: node.insertLayer(0, sl))
        menu.addSeparator()
        s = ""

    def populateDataViewMenu(self, menu: QMenu, dataView: Dock):
        assert isinstance(menu, QMenu)
        if dataView.isVisible():
            a = menu.addAction('Hide View')
            a.triggered.connect(lambda: dataView.setVisible(False))
        else:
            a = menu.addAction('Show View')
            a.triggered.connect(lambda: dataView.setVisible(True))

        a = menu.addAction('Close View')
        a.triggered.connect(lambda: dataView.close())
        return menu


class EnMAPBoxContextMenuRegistry(QObject):
    _instance = None

    @staticmethod
    def instance() -> 'EnMAPBoxContextMenuRegistry':
        if not isinstance(EnMAPBoxContextMenuRegistry._instance, EnMAPBoxContextMenuRegistry):
            EnMAPBoxContextMenuRegistry._instance = EnMAPBoxContextMenuRegistry()
            EnMAPBoxContextMenuRegistry._instance.addProvider(EnMAPBoxContextMenuProvider())
        return EnMAPBoxContextMenuRegistry._instance

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.mProviders: List[EnMAPBoxAbstractContextMenuProvider] = []

    def __len__(self) -> int:
        return len(self.mProviders)

    def __iter__(self) -> Iterator[EnMAPBoxAbstractContextMenuProvider]:
        return iter(self.mProviders)

    def addProvider(self, provider: EnMAPBoxAbstractContextMenuProvider):
        assert isinstance(provider, EnMAPBoxAbstractContextMenuProvider)
        provider.setParent(self)
        self.mProviders.append(provider)

    def removeProvider(self, provider: EnMAPBoxAbstractContextMenuProvider) -> bool:
        assert isinstance(provider, EnMAPBoxAbstractContextMenuProvider)
        if provider in self.mProviders:
            provider.setParent(None)
            self.mProviders.remove(provider)
            return True
        else:
            return False


def populateMapCanvasContextMenu(menu: QMenu,
                                 mapCanvas: MapCanvas,
                                 pos: QPointF,
                                 point: QgsPointXY) -> Tuple[bool, List[str]]:
    for p in EnMAPBoxContextMenuRegistry.instance():
        p: EnMAPBoxContextMenuProvider
        errors = []
        try:
            p.populateMapCanvasMenu(menu, mapCanvas, pos, point)
        except Exception as ex:
            errors.append(str(ex))
    for e in errors:
        messageLog(e, Qgis.MessageLevel.Warning, notifyUser=False)
    return len(errors) == 0, errors


def populateDataViewContextMenu(menu: QMenu, dataview: Dock) -> Tuple[bool, List[str]]:
    for p in EnMAPBoxContextMenuRegistry.instance():
        p: EnMAPBoxContextMenuProvider
        errors = []
        try:
            p.populateDataViewMenu(menu, dataview)
        except Exception as ex:
            errors.append(str(ex))
    for e in errors:
        messageLog(e, Qgis.MessageLevel.Warning, notifyUser=False)
    return len(errors) == 0, errors
