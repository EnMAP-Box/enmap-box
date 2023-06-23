from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMenu
from typing import List, Iterator
from qgis.core import QgsMapLayer, QgsPointXY

from enmapbox.gui.datasources.datasources import DataSource
from enmapbox.gui.dataviews.docks import Dock
from enmapbox.gui.mapcanvas import MapCanvas


class EnMAPBoxContextMenuProvider(object):

    def extendMapLayerMenu(self, menu: QMenu, mapLayer: QgsMapLayer):
        """
        Overwrite to extend the map layer menu
        """
        pass

    def extendMapCanvasMenu(self, menu: QMenu, mapCanvas: MapCanvas, point: QgsPointXY):
        """
        Overwrite to extend the MapCanvas menu
        """
        pass

    def extendDataSourceMenu(self, menu: QMenu, dataSource: DataSource):
        """
        Overwrite to extend a DataSource menu
        """
        pass

    def extendDataViewMenu(self, menu: QMenu, dataView: Dock):
        """
        Overwrite to extend a DataView (aka EnMAP-Box Dock) menu
        """
        pass


class EnMAPBoxContextMenuRegistry(QObject):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.mProviders: List[EnMAPBoxContextMenuProvider] = []

    def __len__(self) -> int:
        return len(self.mProviders)

    def __iter__(self) -> Iterator[EnMAPBoxContextMenuProvider]:
        return iter(self.mProviders)

    def addProvider(self, provider: EnMAPBoxContextMenuProvider):
        assert isinstance(provider, EnMAPBoxContextMenuProvider)
        self.mProviders.append(provider)

    def removeProvider(self, provider: EnMAPBoxContextMenuProvider) -> bool:
        assert isinstance(provider, EnMAPBoxContextMenuProvider)
        if provider in self.mProviders:
            self.mProviders.remove(provider)
            return True
        else:
            return False
