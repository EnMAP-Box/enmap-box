from classificationworkflowapp.classificationworkflowgui import ClassificationWorkflowGui
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon


def enmapboxApplicationFactory(enmapBox):
    return [ClassificationWorkflowApp(enmapBox)]


class ClassificationWorkflowApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = self.title()
        self.version = '2.0'
        self.licence = 'GNU GPL-3'

    def icon(self):
        return QIcon(None)

    def title(self):
        return 'Classification Workflow (advanced)'

    def menu(self, appMenu):
        a = self.utilsAddActionInAlphanumericOrder(self.enmapbox.ui.menuApplicationsClassification, self.title())
        a.triggered.connect(self.startGUI)

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = ClassificationWorkflowGui(parent=self.enmapbox.ui)
        w.show()
