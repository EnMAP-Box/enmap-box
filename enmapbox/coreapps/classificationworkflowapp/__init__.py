from classificationworkflowapp.classificationworkflowgui import ClassificationWorkflowGui
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction


def enmapboxApplicationFactory(enmapBox):
    return [ClassificationWorkflowApp(enmapBox)]


class ClassificationWorkflowApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'ClassificationWorkflowApp'
        self.version = '2.0'
        self.licence = 'GNU GPL-3'

    def icon(self):
        return QIcon(None)

    def menu(self, appMenu):
        assert isinstance(appMenu, QMenu)
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Classification Workflow (advanced)')
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = ClassificationWorkflowGui(parent=self.enmapbox.ui)
        w.show()
