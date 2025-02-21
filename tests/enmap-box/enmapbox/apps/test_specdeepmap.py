from enmapbox import initAll
from enmapbox.apps.SpecDeepMap import RasterSplitterRP
from enmapbox.testing import start_app, TestCase
from qgis.core import QgsProcessingAlgorithm

start_app()
initAll()


class TestSpecDeepMap(TestCase):

    def test_RasterSplitterRP(self):
        alg = RasterSplitterRP()
        self.assertIsInstance(alg, QgsProcessingAlgorithm)
