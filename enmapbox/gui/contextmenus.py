from enmapbox.gui.contextmenuprovider import EnMAPBoxContextMenuProvider
from qgis.PyQt.QtCore import QPoint

from enmapbox import messageLog
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMenu
from typing import List, Iterator, Tuple

from qgis.core import Qgis

from qgis.core import QgsMapLayer, QgsPointXY

from enmapbox.gui.datasources.datasources import DataSource
from enmapbox.gui.dataviews.docks import Dock
from enmapbox.gui.mapcanvas import MapCanvas


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

    def populateMapCanvasMenu(self, menu: QMenu, mapCanvas: MapCanvas, pos: QPoint, point: QgsPointXY):
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


class EnMAPBoxContextMenuRegistry(QObject):
    """
    A registry for EnMAPBoxContextMenuProviders
    """
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


    def populateMapCanvasMenu(self,
                             menu: QMenu,
                             mapCanvas: MapCanvas,
                             pos: QPoint,
                             point: QgsPointXY) -> Tuple[bool, List[str]]:
        for p in EnMAPBoxContextMenuRegistry.instance():
            p: EnMAPBoxContextMenuProvider
            errors = []
            try:
                p.populateMapCanvasMenu(menu, mapCanvas, pos, point)
            except Exception as ex:
                raise Exception
                errors.append(str(ex))
        for e in errors:
            messageLog(e, Qgis.MessageLevel.Critical, notifyUser=False)
        return len(errors) == 0, errors

    def populateDataViewMenu(self,
                             menu: QMenu,
                             dataview: Dock) -> Tuple[bool, List[str]]:
        for p in EnMAPBoxContextMenuRegistry.instance():
            p: EnMAPBoxContextMenuProvider
            errors = []
            try:
                p.populateDataViewMenu(menu, dataview)
            except Exception as ex:
                errors.append(str(ex))
        for e in errors:
            messageLog(e, Qgis.MessageLevel.Critical, notifyUser=False)
        return len(errors) == 0, errors
