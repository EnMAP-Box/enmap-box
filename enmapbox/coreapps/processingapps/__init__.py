from os.path import join, dirname

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction

from enmapbox.gui.applications import EnMAPBoxApplication
from enmapboxprocessing.algorithm.classificationworkflowalgorithm import ClassificationWorkflowAlgorithm
from enmapboxprocessing.algorithm.rastermathalgorithm.rastermathalgorithm import RasterMathAlgorithm
from enmapboxprocessing.algorithm.regressionbasedunmixingalgorithm import RegressionBasedUnmixingAlgorithm
from enmapboxprocessing.algorithm.regressionworkflowalgorithm import RegressionWorkflowAlgorithm
from enmapboxprocessing.algorithm.stackrasterlayersalgorithm import StackRasterLayersAlgorithm


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

        toolMenu: QMenu = self.enmapbox.menu('Tools')

        # apps
        algs = [
            ClassificationWorkflowAlgorithm(), RasterMathAlgorithm(), RegressionBasedUnmixingAlgorithm(),
            RegressionWorkflowAlgorithm()
        ]
        for alg in algs:
            a = self.utilsAddActionInAlphanumericOrder(appMenu, alg.displayName())
            if isinstance(alg, RasterMathAlgorithm):
                a.setIcon(self.numpyIcon())
            else:
                a.setIcon(self.processingIcon())
            a.triggered.connect(self.startAlgorithm)
            a.algorithm = alg

        # tools
        algs = [
            StackRasterLayersAlgorithm()
        ]
        for alg in algs:
            a = self.utilsAddActionInAlphanumericOrder(toolMenu, alg.displayName())
            a.setIcon(self.processingIcon())
            a.triggered.connect(self.startAlgorithm)
            a.algorithm = alg

    def startAlgorithm(self, *args):
        a: QAction = self.sender()
        self.enmapbox.showProcessingAlgorithmDialog(a.algorithm, parent=self.enmapbox.ui)
