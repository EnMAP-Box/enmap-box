from enmapboxtestdata import SensorProducts, sensorProductsRoot
from qgis.testing import TestCase


class TestEnMAPBoxTestdata(TestCase):

    def test(self):
        if sensorProductsRoot() is None:
            return
        print(SensorProducts.Enmap.L1B_MetadataXml)
