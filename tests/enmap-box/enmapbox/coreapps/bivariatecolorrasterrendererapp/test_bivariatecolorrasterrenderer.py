from enmapboxprocessing.testcase import TestCase


class TestDualbandPseudocolorRenderer(TestCase):

    def test(self):
        return  # just a local test
        # layer = QgsRasterLayer(r'D:\data\katja_kowalski\NDFI.vrt', 'NDFI')
        # renderer = BivariateColorRasterRenderer(layer.dataProvider())
        # renderer.setRange(12, 618, 187, 8087)
        # renderer.setBands(1, 2)
        # with open('colorplane.txt') as file:
        #     colorPlane = np.array(eval(file.read()))
        # renderer.setColorPlane(colorPlane)
        # layer.setRenderer(renderer)
        # layer.renderer().block(0, layer.extent(), 100, 100)
