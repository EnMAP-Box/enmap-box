from typing import Optional

from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.typeguard import typechecked
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.gui import QgisInterface
from rastermaskingapp.rastermaskingdockwidget import RasterMaskingDockWidget


def enmapboxApplicationFactory(enmapBox: EnMAPBox):
    return []
    return [RasterMaskingApp(enmapBox, None, None)]


@typechecked
class RasterMaskingApp(EnMAPBoxApplication):

    def __init__(self, enmapBox: Optional[EnMAPBox], interface: Optional[QgisInterface], parent=None):
        super().__init__(enmapBox, parent=parent)

        if interface is None:
            interface = enmapBox
        self.interface = interface
        self.isEnmapInterface = isinstance(interface, EnMAPBox)

        self.name = RasterMaskingApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

        self.initGui()

    @classmethod
    def icon(cls):
        return QIcon(__file__.replace('__init__.py', '/icon.svg'))

    def initGui(self):
        self.initEnmapOrQgisGui(self.interface)

    def initEnmapOrQgisGui(self, interface: QgisInterface):

        # add toolbar button
        self.actionToggleDock = QAction(self.icon(), 'Raster Masking')
        self.actionToggleDock.triggered.connect(self.toggleDockVisibility)

        # add main dock and toolbar button
        self.dock = RasterMaskingDockWidget(parent=self.parent())
        interface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.dock.setWindowIcon(self.icon())
        self.dock.hide()

        if self.isEnmapInterface:
            interface.ui.mEo4qToolbar.addAction(self.actionToggleDock)
        else:
            interface.addToolBarIcon(self.actionToggleDock)

        self.dock.setInterface(interface)

    def toggleDockVisibility(self):
        self.dock.setUserVisible(not self.dock.isUserVisible())
