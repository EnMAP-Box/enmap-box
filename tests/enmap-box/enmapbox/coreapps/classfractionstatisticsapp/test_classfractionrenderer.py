import numpy as np
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRasterLayer, Qgis

from classfractionstatisticsapp.classfractionrenderer import ClassFractionRenderer
from enmapbox import initAll
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import fraction_map_l3
from enmapboxtestdata import landcover_map_l3

start_app()
initAll()


class TestClassFractionRenderer(TestCase):

    def test_fractionL3(self):
        classification = QgsRasterLayer(landcover_map_l3)
        self.assertTrue(classification.isValid())

        categories = Utils.categoriesFromPalettedRasterRenderer(classification.renderer())
        colors = [QColor(category.color) for category in categories]

        raster = QgsRasterLayer(fraction_map_l3)
        renderer = ClassFractionRenderer(raster.dataProvider())
        renderer.setColors(colors)

        raster.setRenderer(renderer)
        block = renderer.block(1, raster.extent(), raster.width(), raster.height())
        self.assertEqual(Qgis.ARGB32_Premultiplied, block.dataType())
        self.assertEqual(305025900183086, np.sum(Utils.qgsRasterBlockToNumpyArray(block), dtype=float))
