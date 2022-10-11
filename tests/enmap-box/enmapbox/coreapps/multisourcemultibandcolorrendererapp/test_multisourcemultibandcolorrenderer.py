from enmapboxprocessing.test.testcase import TestCase
from enmapboxtestdata import enmap
from multisourcemultibandcolorrendererapp.multisourcemultibandcolorrenderer import MultiSourceMultiBandColorRenderer
from qgis.core import QgsRasterLayer


class TestMultiSourceMultiBandColorRenderer(TestCase):

    def test(self):
        layer = QgsRasterLayer(enmap)
        renderer = MultiSourceMultiBandColorRenderer(layer.dataProvider())
        renderer.setRange(0, 0, 0, 10000, 10000, 10000)
        renderer.setBands(1, 2, 3)
        renderer.setSources(enmap, enmap, enmap)
        layer.setRenderer(renderer)
        layer.renderer().block(0, layer.extent(), 100, 100)
