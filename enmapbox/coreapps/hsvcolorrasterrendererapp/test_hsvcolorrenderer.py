from enmapboxprocessing.test.testcase import TestCase
from hsvcolorrasterrendererapp.hsvcolorrasterrenderer import HsvColorRasterRenderer
from qgis.core import QgsRasterLayer


class TestHsvColorRenderer(TestCase):

    def test(self):
        layer = QgsRasterLayer(
            r'D:\data\matthias_wocher\Irlbach_20210530_AVIRIS_NG_simulated_EnMAP_233Bands\ang20210530t101445_rfl_wlCut_ASI_3band_car_cab_h2o.bsq')

        if self.fileExists(layer.source()):
            return

        renderer = HsvColorRasterRenderer(layer.dataProvider())
        renderer.setRange(0, 0, 0, 0.0761372, 0.368215, 0.0156974)
        renderer.setBands(1, 2, 3)
        layer.setRenderer(renderer)
        layer.renderer().block(0, layer.extent(), 100, 100)
