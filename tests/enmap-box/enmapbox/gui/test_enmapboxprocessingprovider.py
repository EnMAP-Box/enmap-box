import unittest

from enmapbox import initAll
from enmapbox.testing import TestCase, TestObjects, start_app
from qgis.core import QgsApplication, QgsProcessingRegistry, QgsProcessingAlgorithm, QgsProcessingProvider

start_app()
initAll()


class ProcessingProviderTests(TestCase):

    def test_processing_provider(self):
        from enmapbox.algorithmprovider import EnMAPBoxProcessingProvider
        reg = QgsApplication.instance().processingRegistry()
        self.assertIsInstance(reg, QgsProcessingRegistry)

        provider = EnMAPBoxProcessingProvider()
        test_name = 'EnMAPBoxTextProvider'
        test_id = 'EnMAPBoxTextProviderID'
        provider.name = lambda: test_name
        provider.id = lambda: test_id

        self.assertIsInstance(provider, QgsProcessingProvider)
        self.assertTrue(len(provider.algorithms()) == 0)

        self.assertTrue(provider not in reg.providers())
        reg.addProvider(provider)
        self.assertTrue(provider in reg.providers())

        self.assertTrue(provider in reg.providers())

        alg = TestObjects.processingAlgorithm()
        self.assertTrue(alg, QgsProcessingAlgorithm)
        provider.addAlgorithm(alg)
        self.assertTrue(alg in provider.algorithms())
        self.assertTrue(alg in reg.algorithms())

        reg.removeProvider(provider)
        self.assertTrue(provider not in reg.providers())
        self.assertTrue(alg not in reg.algorithms())


if __name__ == "__main__":
    unittest.main(buffer=False)
