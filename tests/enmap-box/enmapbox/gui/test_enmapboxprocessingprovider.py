import sys
import unittest

from qgis.core import QgsApplication, QgsProcessingAlgorithm, QgsProcessingProvider, QgsProcessingRegistry
from enmapbox.testing import start_app, TestCase, TestObjects
from enmapbox.algorithmprovider import EnMAPBoxProcessingProvider
from qgis.PyQt import sip

start_app()


class ProcessingProviderTests(TestCase):

    def test_processing_provider(self):

        reg = QgsApplication.instance().processingRegistry()

        provider = EnMAPBoxProcessingProvider()

        self.assertIsInstance(provider, QgsProcessingProvider)
        self.assertTrue(len(provider.algorithms()) == 0)

        self.assertIsInstance(reg, QgsProcessingRegistry)
        self.assertTrue(provider not in reg.providers())
        reg.addProvider(provider)
        if provider not in reg.providers():
            print('Provider not in registry:\n{}'.format(str(provider)), file=sys.stderr)
            for p2 in reg.providers():
                print(p2)

        self.assertTrue(provider in reg.providers())

        alg = TestObjects.processingAlgorithm()
        self.assertTrue(alg, QgsProcessingAlgorithm)
        provider.addAlgorithm(alg)
        self.assertTrue(alg in provider.algorithms())
        self.assertTrue(alg in reg.algorithms())

        self.assertFalse(sip.isdeleted(provider))
        reg.removeProvider(provider)
        QgsApplication.processEvents()
        self.assertTrue(sip.isdeleted(provider))

        self.assertTrue(provider not in reg.providers())
        self.assertTrue(alg not in reg.algorithms())

    def test_init(self):

        from enmapbox import registerEnMAPBoxProcessingProvider, unregisterEnMAPBoxProcessingProvider
        from enmapbox.algorithmprovider import EnMAPBoxProcessingProvider, ID

        registry = QgsApplication.instance().processingRegistry()
        self.assertIsInstance(registry, QgsProcessingRegistry)

        n1 = len(registry.algorithms())
        registerEnMAPBoxProcessingProvider()

        enmapBoxProvider = registry.providerById(ID)
        self.assertIsInstance(enmapBoxProvider, EnMAPBoxProcessingProvider)
        del enmapBoxProvider
        n2 = len(registry.algorithms())
        self.assertTrue(n2 > n1)
        unregisterEnMAPBoxProcessingProvider()

        n3 = len(registry.algorithms())
        self.assertEqual(n1, n3)
        s = ""


if __name__ == "__main__":
    unittest.main(buffer=False)
