from typing import Optional

from qgis.PyQt.QtWidgets import QComboBox

from enmapbox.gui.dataviews.docks import MapDock, DockTypes
from typeguard import typechecked


@typechecked
class MapViewComboBox(QComboBox):

    def __init__(self, parent=None):
        from enmapbox import EnMAPBox
        super().__init__(parent)

        self._emptyText = ''

        self.enmapBox = EnMAPBox.instance()
        self.enmapBox.mDockManager.sigDockRemoved.connect(self.onMapViewsChanged)
        self.enmapBox.mDockManager.sigDockAdded.connect(self.onMapViewsChanged)
        self.enmapBox.mDockManager.sigDockTitleChanged.connect(self.onMapViewsChanged)

        self.onMapViewsChanged()

    def setEmptyText(self, text: str):
        self._emptyText = text
        self.setItemText(0, text)

    def setMapView(self, mapView: MapDock):
        self.mapView = mapView

    def currentMapView(self) -> Optional[MapDock]:
        mapDocks = self.enmapBox.docks(DockTypes.MapDock)
        mapDocks.insert(0, None)
        return mapDocks[self.currentIndex()]

    def onMapViewsChanged(self):
        index = self.currentIndex()
        name = self.currentText()
        names = [mapView.title() for mapView in self.enmapBox.docks(DockTypes.MapDock)]
        names.insert(0, self._emptyText)
        aMapViewWasRenamed = self.count() == names
        self.clear()
        self.addItems(names)

        if aMapViewWasRenamed:  # set to old index
            self.setCurrentIndex(index)
        else:
            if name in names:  # try to set old map view by matching names
                self.setCurrentIndex(names.index(name))
            else:
                self.setCurrentIndex(0)
