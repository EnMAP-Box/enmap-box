from enmapboxtestdata import SensorProducts
from qgis.testing import TestCase


class TestEnmapboxtestdata(TestCase):

    def test(self):
        print(SensorProducts.Enmap.L1B_MetadataXml)
