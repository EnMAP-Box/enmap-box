import numpy as np

from bivariatecolorrasterrendererapp.bivariatecolorrasterrenderer import BivariateColorRasterRenderer
from enmapboxprocessing.test.testcase import TestCase
from qgis.core import QgsRasterLayer


class TestDualbandPseudocolorRenderer(TestCase):

    def test(self):
        layer = QgsRasterLayer(r'D:\data\katja_kowalski\NDFI.vrt', 'NDFI')
        renderer = BivariateColorRasterRenderer(layer.dataProvider())
        renderer.setRange(12, 618, 187, 8087)
        renderer.setBands(1, 2)
        with open('colorplane.txt') as file:
            colorPlane = np.array(eval(file.read()))
        renderer.setColorPlane(colorPlane)
        layer.setRenderer(renderer)
        layer.renderer().block(0, layer.extent(), 100, 100)
