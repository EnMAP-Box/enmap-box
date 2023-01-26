from typing import Optional

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.gui.dataviews.docks import DockTypes, MapDock
from enmapbox.gui.mapcanvas import CanvasLink
from enmapbox.utils import isEarthEngineModuleInstalled
from geetimeseriesexplorerapp.externals.ee_plugin.provider import register_data_provider
from geetimeseriesexplorerapp.geetemporalprofiledockwidget import GeeTemporalProfileDockWidget
from geetimeseriesexplorerapp.geetimeseriesexplorerdockwidget import GeeTimeseriesExplorerDockWidget
from geetimeseriesexplorerapp.maptool import MapTool
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsRasterLayer, QgsRectangle, QgsProject
from qgis.gui import QgisInterface
from typeguard import typechecked


def enmapboxApplicationFactory(enmapBox: EnMAPBox):
    app = GeeTimeseriesExplorerApp(enmapBox, None, None)
    return [app]


@typechecked
class GeeTimeseriesExplorerApp(EnMAPBoxApplication):

    def __init__(
            self, enmapBox: Optional[EnMAPBox], interface: Optional[QgisInterface],
            currentLocationMapTool: Optional[MapTool], parent=None
    ):
        super().__init__(enmapBox, parent=parent)

        if interface is None:
            interface = enmapBox
        self.interface = interface
        self.isEnmapInterface = isinstance(interface, EnMAPBox)
        self.currentLocationMapTool = currentLocationMapTool

        self.name = GeeTimeseriesExplorerApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

        self.backgroundLayer = QgsRasterLayer(
            'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0',
            'Google Maps', 'wms'
        )

        # Create and register the EE data providers
        register_data_provider()

        self.initGui()

    @classmethod
    def icon(cls):
        return QIcon(__file__.replace('__init__.py', '/icon.svg'))

    def initGui(self):
        self.initEnmapOrQgisGui(self.interface)

    def initEnmapOrQgisGui(self, interface: QgisInterface):

        # add toolbar button
        self.actionToggleMainDock = QAction(self.icon(), 'GEE Time Series Explorer')
        self.actionToggleMainDock.triggered.connect(self.toggleMainDockVisibility)

        # add main dock and toolbar button
        self.mainDock = GeeTimeseriesExplorerDockWidget(parent=self.parent())
        interface.addDockWidget(Qt.RightDockWidgetArea, self.mainDock)
        self.mainDock.setWindowIcon(self.icon())
        self.mainDock.hide()

        if self.isEnmapInterface:
            interface.ui.mEo4qToolbar.addAction(self.actionToggleMainDock)
        else:
            interface.addToolBarIcon(self.actionToggleMainDock)

        # add profile dock
        self.profileDock = GeeTemporalProfileDockWidget(self.mainDock)
        interface.addDockWidget(Qt.TopDockWidgetArea, self.profileDock)
        self.profileDock.setWindowIcon(self.icon())
        self.profileDock.hide()

        # set some members
        self.mainDock.setProfileDock(self.profileDock)
        self.mainDock.setInterface(interface)

        # connect signals
        if not self.isEnmapInterface:
            self.currentLocationMapTool.sigClicked.connect(self.profileDock.setCurrentLocationFromQgsMapMouseEvent)

    def toggleMainDockVisibility(self):

        if not isEarthEngineModuleInstalled():
            self.mainDock.setVisible(False)
            self.profileDock.setVisible(False)
            return

        self.mainDock.setVisible(not self.mainDock.isVisible())
        self.profileDock.setVisible(self.mainDock.isVisible())

        if isinstance(self.interface, EnMAPBox):
            if len(self.enmapbox.docks(DockTypes.MapDock)) == 0:
                self.newEnmapBoxMapView()
        else:
            from qgis.utils import iface
            if iface.mapCanvas().layerCount() == 0:
                QgsProject.instance().addMapLayer(self.backgroundLayer.clone())

    def newEnmapBoxMapView(self):
        currentMapDock = self.enmapbox.currentMapDock()

        mapDock: MapDock = self.enmapbox.createDock(DockTypes.MapDock)
        mapDock.addLayers([self.backgroundLayer.clone()])

        if currentMapDock is None:  # zoom to Germany
            germany = QgsRectangle(633652, 5971168, 1766199, 7363456)
            mapDock.mapCanvas().setExtent(germany)
        else:
            currentMapDock.linkWithMapDock(mapDock, CanvasLink.LINK_ON_CENTER_SCALE)
