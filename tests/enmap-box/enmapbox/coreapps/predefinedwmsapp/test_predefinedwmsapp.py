from enmapboxprocessing.testcase import TestCase
from predefinedwmsapp import PredefinedWmsApp
from qgis.core import QgsRasterLayer


class TestPredefinedWmsApp(TestCase):

    def test(self):
        for name, uri in PredefinedWmsApp.WMS:
            layer = QgsRasterLayer(uri, name, 'WMS')
            self.assertTrue(layer.isValid())
