"""
This is a template to create an EnMAP-Box test
"""
import unittest

from qgis.core import QgsProcessingRegistry, QgsApplication, QgsProcessingContext

from enmapbox.testing import EnMAPBoxTestCase
from enmapboxprocessing.algorithm.spectralresamplingtoprismaalgorithm import SpectralResamplingToPrismaAlgorithm


class EnMAPBoxTestCaseExample(EnMAPBoxTestCase):

    def test_parameterization_strings(self):
        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        alg = reg.algorithmById('enmapbox:SpectralResamplingToPrisma')
        self.assertIsInstance(alg, SpectralResamplingToPrismaAlgorithm)
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
