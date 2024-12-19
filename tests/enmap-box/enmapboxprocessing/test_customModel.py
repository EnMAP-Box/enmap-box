from os.path import join, basename
from shutil import copyfile

from qgis.core import QgsApplication

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import custom_model, SensorProducts, sensorProductsRoot


class TestCustomModel(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        profileFolder = join(QgsApplication.qgisSettingsDirPath(), 'processing', 'models')
        copyfile(custom_model, join(profileFolder, basename(custom_model)))

        alg = 'model:importEnmapL2'
        parameters = {
            'enmap_l2_xml_file': SensorProducts.Enmap.L2A_MetadataXml,
            'enmap_l2_raster': self.filename('enmalL2.vrt')
        }
        self.runalg(alg, parameters)
