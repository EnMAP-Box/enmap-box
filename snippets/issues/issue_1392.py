import unittest

from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from qgis.gui import QgsMapCanvas, QgsRasterLayerProperties


class Issue1392Tests(EnMAPBoxTestCase):

    def test_dialog(self):
        from enmapbox import registerMapLayerConfigWidgetFactories
        registerMapLayerConfigWidgetFactories()

        layer = TestObjects.createRasterLayer()
        canvas = QgsMapCanvas()
        canvas.setLayers([layer])

        d = QgsRasterLayerProperties(layer, canvas)

        self.showGui(d)
        pass

    if __name__ == '__main__':
        unittest.main(buffer=False)
