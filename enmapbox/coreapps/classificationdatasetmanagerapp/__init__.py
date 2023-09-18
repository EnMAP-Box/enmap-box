from classificationdatasetmanagerapp.classificationdatasetmanagergui import ClassificationDatasetManagerGui
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon


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

    def title(self):
        return 'Classification Dataset Manager'

    def menu(self, appMenu):
        a = self.utilsAddActionInAlphanumericOrder(
            self.enmapbox.ui.menuApplicationsClassification, self.title() + ' (and Random Subsampling)'
        )
        a.triggered.connect(self.startGUI)

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = ClassificationDatasetManagerGui(parent=self.enmapbox.ui)
        w.show()
