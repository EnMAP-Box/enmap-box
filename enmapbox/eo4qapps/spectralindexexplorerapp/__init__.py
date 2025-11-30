from typing import Optional, List

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProcessingAlgorithm
from qgis.gui import QgisInterface

from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.typeguard import typechecked
from spectralindexexplorerapp.spectralindexexplorerdockwidget import SpectralIndexExplorerDockWidget
from spectralindexexplorerapp.spectralindexlayeralgorithm import SpectralIndexLayerAlgorithm


def enmapboxApplicationFactory(enmapBox: EnMAPBox):
    return [SpectralIndexExplorerApp(enmapBox, None, None)]


@typechecked
class SpectralIndexExplorerApp(EnMAPBoxApplication):

    def __init__(
            self, enmapBox: Optional[EnMAPBox], interface: Optional[QgisInterface], parent=None
    ):
        super().__init__(enmapBox, parent=parent)

        if interface is None:
            interface = enmapBox
        self.interface = interface
        self.isEnmapInterface = isinstance(interface, EnMAPBox)
        self.name = SpectralIndexExplorerApp.__name__
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
        self.actionToggleDock = QAction(self.icon(), 'Spectral Index Explorer')
        self.actionToggleDock.triggered.connect(self.toggleDockVisibility)

        # add main dock and toolbar button
        self.dock = SpectralIndexExplorerDockWidget(parent=self.parent())
        interface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.setWindowIcon(self.icon())
        self.dock.hide()

        if self.isEnmapInterface:
            interface.ui.mEo4qToolbar.addAction(self.actionToggleDock)
        else:
            interface.addToolBarIcon(self.actionToggleDock)

        self.dock.setInterface(interface)

    def toggleDockVisibility(self):
        self.dock.setVisible(not self.dock.isVisible())

    def processingAlgorithms(self) -> List[QgsProcessingAlgorithm]:
        return [SpectralIndexLayerAlgorithm()]
