from qgis.PyQt.QtGui import QColor

from classfractionstatisticsapp.classfractionrenderer import ClassFractionRenderer
from qgis.core import QgsRasterLayer, Qgis
import numpy as np


from enmapboxprocessing.test.testcase import TestCase
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import landcover_map_l3
from enmapboxtestdata import fraction_map_l3


class TestClassFractionRenderer(TestCase):

    def test_fractionL3(self):
        classification = QgsRasterLayer(landcover_map_l3)
        categories = Utils.categoriesFromPalettedRasterRenderer(classification.renderer())
        colors = [QColor(category.color) for category in categories]

        raster = QgsRasterLayer(fraction_map_l3)
        renderer = ClassFractionRenderer(raster.dataProvider())
        renderer.setColors(colors)

        raster.setRenderer(renderer)
        block = renderer.block(1, raster.extent(), raster.width(), raster.height())
        self.assertEqual(Qgis.ARGB32_Premultiplied, block.dataType())
        self.assertEqual(305025900183086, np.sum(Utils.qgsRasterBlockToNumpyArray(block), dtype=float))
