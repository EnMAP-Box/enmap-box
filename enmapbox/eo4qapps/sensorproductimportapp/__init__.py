from typing import Optional

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.gui import QgisInterface
from sensorproductimportapp.sensorproductimportdockwidget import SensorProductImportDockWidget
from typeguard import typechecked


def enmapboxApplicationFactory(enmapBox: EnMAPBox):
    return [SensorProductImportApp(enmapBox, None, None)]


@typechecked
class SensorProductImportApp(EnMAPBoxApplication):

    def __init__(
            self, enmapBox: Optional[EnMAPBox], interface: Optional[QgisInterface], parent=None
    ):
        super().__init__(enmapBox, parent=parent)

        if interface is None:
            interface = enmapBox
        self.interface = interface
        self.isEnmapInterface = isinstance(interface, EnMAPBox)

        self.name = SensorProductImportApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

        self.initGui()

    @classmethod
    def icon(cls):
        return QIcon(__file__.replace('__init__.py', '/icon.png'))

    def initGui(self):
        self.initEnmapOrQgisGui(self.interface)

    def initEnmapOrQgisGui(self, interface: QgisInterface):

        # add toolbar button
        self.actionToggleDock = QAction(self.icon(), 'Sensor Product Import')
        self.actionToggleDock.triggered.connect(self.toggleDockVisibility)

        # add main dock and toolbar button
        self.dock = SensorProductImportDockWidget(parent=self.parent())
        interface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.dock.setWindowIcon(self.icon())
        self.dock.hide()

        if self.isEnmapInterface:
            interface.ui.mEo4qToolbar.addAction(self.actionToggleDock)
        else:
            interface.addToolBarIcon(self.actionToggleDock)

        self.dock.setInterface(interface)

    def onCurrentLocationMapToolClicked(self):
        if self.actionCurrentLocationMapTool.isChecked():
            self.interface.mapCanvas().setMapTool(self.currentLocationMapTool)
        else:
            self.interface.mapCanvas().unsetMapTool(self.currentLocationMapTool)

    def toggleDockVisibility(self):
        self.dock.setUserVisible(not self.dock.isUserVisible())
