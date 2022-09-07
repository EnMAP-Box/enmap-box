import unittest
from os.path import dirname, join, exists
from typing import Dict

from enmapbox.testing import start_app
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
from processing.core.Processing import Processing
from qgis.core import QgsProcessingFeedback

qgsApp = start_app()


class ProcessingFeedback(QgsProcessingFeedback):
    def setProgress(self, progress):
        print('\r', round(progress, 5), end='%', flush=True)
        if progress == 100:
            print('\r', end='')


class TestCase(unittest.TestCase):
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

    def filename(self, basename: str):
        import enmapbox
        return join(dirname(dirname(enmapbox.__file__)), 'test-outputs', basename)

    def additionalDataFolderExists(self):
        return exists(r'D:\data')
