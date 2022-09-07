from classificationdatasetmanagerapp.classificationdatasetmanagergui import ClassificationDatasetManagerGui
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction


def enmapboxApplicationFactory(enmapBox):
    return [ClassificationDatasetManagerApp(enmapBox)]


class ClassificationDatasetManagerApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'ClassificationDatasetManager'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def icon(self):
        return QIcon(None)

    def menu(self, appMenu):
        assert isinstance(appMenu, QMenu)
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Classification Dataset Manager')
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = ClassificationDatasetManagerGui(parent=self.enmapbox.ui)
        w.show()
