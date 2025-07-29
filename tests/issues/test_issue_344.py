"""
This is a template to create an EnMAP-Box test
"""
import unittest

from enmapbox.testing import EnMAPBoxTestCase
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingRegistry, QgsApplication, QgsProcessingContext


class EnMAPBoxTestCaseExample(EnMAPBoxTestCase):

    def test_parameterization_strings(self):
        aid = 'enmapbox:SpectralResamplingToPrisma'.lower()
        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        alg: QgsProcessingAlgorithm = reg.algorithmById(aid)

        if not isinstance(alg, QgsProcessingAlgorithm):
            self.skipTest(f'Unable to load {aid} from processing registry.')

        configuration = {}

        alg.initAlgorithm(configuration)

        context = QgsProcessingContext()

        parameters = dict()
        pythonCmd = alg.asPythonCommand(parameters, context)
        cliCmd, success = alg.asQgisProcessCommand(parameters, context)
        self.assertEqual(pythonCmd, f"processing.run(\"{alg.id()}\", {{}})")
        self.assertEqual(cliCmd, f"qgis_process run {alg.id()}")
        self.assertTrue(success)


if __name__ == '__main__':
    unittest.main(buffer=False)
