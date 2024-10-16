from os.path import join, dirname

from enmapbox.gui.applications import EnMAPBoxApplication
from enmapboxapplications.imagemathapp.core import ImageMathApp
from enmapboxapplications.regressionapp.core import RegressionWorkflowApp
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction


def enmapboxApplicationFactory(enmapBox):
    return [
        EnMAPBoxImageMathApp(enmapBox),
        EnMAPBoxRegressionWorkflowApp(enmapBox),
    ]


class EnMAPBoxImageMathApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'ImageMath'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def icon(self):
        filename = join(dirname(__file__), 'imagemathapp', 'icons', 'numpy.png')
        return QIcon(filename)

    def menu(self, appMenu):
        assert isinstance(appMenu, QMenu)
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Image Math (deprecated)')
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = ImageMathApp(parent=self.enmapbox.ui)
        w.addInput()
        w.show()


class EnMAPBoxRegressionWorkflowApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'RegressionWorkflowApp'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def icon(self):
        return QIcon(None)

    def menu(self, appMenu):
        a = self.utilsAddActionInAlphanumericOrder(
            self.enmapbox.ui.menuApplicationsRegression, 'Regression Workflow (deprecated)'
        )
        a.triggered.connect(self.startGUI)

    def geoAlgorithms(self):
        return []

    def startGUI(self, *args):
        w = RegressionWorkflowApp(parent=self.enmapbox.ui)
        w.show()
