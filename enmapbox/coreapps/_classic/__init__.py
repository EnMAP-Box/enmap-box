from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction

from _classic.classificationapp.core import ClassificationWorkflowApp
from enmapbox.gui.applications import EnMAPBoxApplication

def enmapboxApplicationFactory(enmapBox):
    return [ClassificationWorkflowClassicApp(enmapBox)]

class ClassificationWorkflowClassicApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'ClassificationWorkflowClassicApp'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def icon(self):
        return QIcon(None)

    def menu(self, appMenu):
        assert isinstance(appMenu, QMenu)
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Classification Workflow (deprecated)')

        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = ClassificationWorkflowApp(parent=self.enmapbox.ui)
        w.show()
