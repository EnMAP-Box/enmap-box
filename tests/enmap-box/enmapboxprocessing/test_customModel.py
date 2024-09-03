from os.path import join, basename
from shutil import copyfile

from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import custom_model
from qgis.core import QgsApplication


class TestCustomModel(TestCase):

    def test(self):
        profileFolder = join(QgsApplication.qgisSettingsDirPath(), 'processing', 'models')
        copyfile(custom_model, join(profileFolder, basename(custom_model)))

        start_app()
        initAll()

        alg = 'model:importEnmapL2'
        parameters = {
            'enmap_l2_xml_file': r'D:\data\sensors\enmap\ENMAP01-____L2A-DT0000004135_20221005T023547Z_010_V010106_20221014T102749Z\ENMAP01-____L2A-DT0000004135_20221005T023547Z_010_V010106_20221014T102749Z-METADATA.XML',
            'enmap_l2_raster': self.filename('enmalL2.vrt')
        }
        self.runalg(alg, parameters)
