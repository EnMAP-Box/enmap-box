from typing import Dict

from enmapbox.testing import start_app
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
from enmapboxprocessing.test.testcase import TestCase as TestCase_
from processing.core.Processing import Processing
from qgis.core import QgsProcessingFeedback

qgsApp = start_app()


class ProcessingFeedback(QgsProcessingFeedback):
    def setProgress(self, progress):
        print('\r', round(progress, 5), end='%', flush=True)
        if progress == 100:
            print('\r', end='')


class TestCase(TestCase_):
    openReport = True

    @staticmethod
    def runalg(alg: EnMAPProcessingAlgorithm, parameters: Dict):
        print(f'\n{"#" * 80}')
        if isinstance(alg, EnMAPProcessingAlgorithm):
            alg.initAlgorithm(configuration=None)
            print(alg.__class__.__name__,
                  '({} -> {}), {}, {}'.format(alg.group(), alg.displayName(), alg.groupId(), alg.name()))
            print('parameters = {}'.format(repr(parameters)))
        return Processing.runAlgorithm(alg, parameters=parameters, feedback=ProcessingFeedback())
