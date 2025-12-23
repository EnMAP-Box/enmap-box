from os.path import join, dirname

from enmapbox.gui.applications import EnMAPBoxApplication
from enmapboxprocessing.algorithm.classificationworkflowalgorithm import ClassificationWorkflowAlgorithm
from enmapboxprocessing.algorithm.rastermathalgorithm.rastermathalgorithm import RasterMathAlgorithm
from enmapboxprocessing.algorithm.regressionbasedunmixingalgorithm import RegressionBasedUnmixingAlgorithm
from enmapboxprocessing.algorithm.regressionworkflowalgorithm import RegressionWorkflowAlgorithm
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction


def enmapboxApplicationFactory(enmapBox):
    return [ProcessingApps(enmapBox)]


class ProcessingApps(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'ProcessingApps'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def processingIcon(self):
        return QIcon(':/images/themes/default/processingAlgorithm.svg')

    def numpyIcon(self):
        return QIcon(join(dirname(__file__), 'numpy.png'))

    def menu(self, appMenu: QMenu):
        algsAndMenus = [
            (ClassificationWorkflowAlgorithm(), self.enmapbox.ui.menuApplicationsClassification),
            (RasterMathAlgorithm(), self.enmapbox.ui.menuApplications),
            (RegressionBasedUnmixingAlgorithm(), self.enmapbox.ui.menuApplicationsUnmixing),
            (RegressionWorkflowAlgorithm(), self.enmapbox.ui.menuApplicationsRegression),
        ]
        for alg, menu in algsAndMenus:
            a = self.utilsAddActionInAlphanumericOrder(menu, alg.displayName())
            a.setIcon(self.processingIcon())
            if isinstance(alg, RasterMathAlgorithm):
                a.setIcon(self.numpyIcon())
            a.triggered.connect(self.startAlgorithm)
            a.algorithm = alg

    def startAlgorithm(self, *args):
        a: QAction = self.sender()
        self.enmapbox.showProcessingAlgorithmDialog(a.algorithm, parent=self.enmapbox.ui)
