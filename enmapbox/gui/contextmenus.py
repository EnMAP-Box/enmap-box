from typing import List, Iterator, Dict, Union

from enmapbox import messageLog
from enmapbox.gui.datasources.datasources import DataSource
from enmapbox.gui.datasources.datasourcesets import DataSourceSet
from enmapbox.gui.datasources.manager import DataSourceManagerTreeView
from enmapbox.gui.dataviews.dockmanager import DockTreeView
from enmapbox.gui.mapcanvas import MapCanvas
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtCore import QPoint
from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsPointXY, Qgis, QgsLayerTreeNode


class EnMAPBoxAbstractContextMenuProvider(QObject):

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def enmapBox(self) -> 'EnMAPBox':
        from enmapbox.gui.enmapboxgui import EnMAPBox
        return EnMAPBox.instance()

    def populateMapCanvasMenu(self, menu: QMenu, mapCanvas: MapCanvas, pos: QPoint, point: QgsPointXY):
        """
        Overwrite to extend the MapCanvas menu
        """
        pass

    def populateDataSourceMenu(self,
                               menu: QMenu,
                               treeView: DataSourceManagerTreeView,
                               selectedNodes: List[Union[DataSourceSet, DataSource]]):
        """
        Overwrite to extend a DataSource menu
        """
        pass

    def populateDataViewMenu(self, menu: QMenu, view: DockTreeView, node: QgsLayerTreeNode):
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
        return EnMAPBoxContextMenuRegistry._instance

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.mProviders: List[EnMAPBoxAbstractContextMenuProvider] = []
        self.mErrorCache: Dict[str, Exception] = dict()
        self.mErrorList: List[Exception] = list()
        self.mRaiseErrors: bool = False

    def setRaiseErrors(self, b: bool):
        """
        Set this on True to raise errors immediately instead of writing the to the log (default).
        """
        self.mRaiseErrors = b

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

    def logError(self, exception: Exception):

        if self.mRaiseErrors:
            raise exception
        else:
            self.mErrorList.append(exception)
            messageLog(f'{exception.__class__.__name__}:"{exception}"', Qgis.MessageLevel.Critical, notifyUser=False)

    def populateMapCanvasMenu(self,
                              menu: QMenu,
                              mapCanvas: MapCanvas,
                              pos: QPoint,
                              point: QgsPointXY) -> bool:
        self.mErrorList.clear()
        import enmapbox
        for p in self:
            try:
                p.populateMapCanvasMenu(menu, mapCanvas, pos, point)
            except Exception as ex:
                self.logError(ex)
                if enmapbox.RAISE_ALL_EXCEPTIONS:
                    raise ex
        return len(self.mErrorList) == 0

    def populateDataViewMenu(self,
                             menu: QMenu,
                             view: DockTreeView,
                             node: QgsLayerTreeNode) -> bool:
        self.mErrorList.clear()
        import enmapbox
        for p in self:
            try:
                p.populateDataViewMenu(menu, view, node)
            except Exception as ex:
                self.logError(ex)
                if enmapbox.RAISE_ALL_EXCEPTIONS:
                    raise ex
        return len(self.mErrorList) == 0

    def populateDataSourceMenu(self,
                               menu: QMenu,
                               treeView: DataSourceManagerTreeView,
                               selectedNodes: List[Union[DataSourceSet, DataSource]]) -> bool:
        self.mErrorList.clear()
        import enmapbox
        for p in self:
            try:
                p.populateDataSourceMenu(menu, treeView, selectedNodes)
            except Exception as ex:
                self.logError(ex)
                if enmapbox.RAISE_ALL_EXCEPTIONS:
                    raise ex
        return len(self.mErrorList) == 0
