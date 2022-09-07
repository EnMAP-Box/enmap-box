from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction
from regressiondatasetmanagerapp.regressiondatasetmanagergui import RegressionDatasetManagerGui


def enmapboxApplicationFactory(enmapBox):
    return [RegressioDatasetManagerApp(enmapBox)]


class RegressioDatasetManagerApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'RegressionDatasetManager'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def icon(self):
        return QIcon(None)

    def menu(self, appMenu):
        assert isinstance(appMenu, QMenu)
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Regression Dataset Manager')
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = RegressionDatasetManagerGui(parent=self.enmapbox.ui)
        w.show()
