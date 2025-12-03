from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu

from eniccsapp.eniccscloudmaskalgorithm import EniccsCloudMaskAlgorithm
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.typeguard import typechecked


def enmapboxApplicationFactory(enmapBox):
    return [EniccsApp(enmapBox)]


@typechecked
class EniccsApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = EniccsApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon()

    @classmethod
    def title(cls):
        return 'EnICCS - EnMAP L2A cloud and cloud shadow mask'

    def menu(self, appMenu: QMenu):
        pass

    def startGUI(self):
        pass

    def processingAlgorithms(self):
        return [EniccsCloudMaskAlgorithm()]
