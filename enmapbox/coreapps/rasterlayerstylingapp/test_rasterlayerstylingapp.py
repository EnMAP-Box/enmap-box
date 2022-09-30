from os.path import basename

import numpy as np

from enmapbox import EnMAPBox, initAll
from enmapbox.testing import start_app
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase
from qgis.core import QgsRasterLayer
from rasterlayerstylingapp import RasterLayerStylingApp


class TestRasterLayerStyling(TestCase):

    def test_editBadBandMultiplier(self):
        # create a dummy raster
        filename = self.filename('raster.tif')
        Driver(filename).createFromArray(np.zeros((3, 10, 10)))

        # create two layer with the same source
        layer = QgsRasterLayer(filename, basename(filename))
        layer2 = QgsRasterLayer(filename, basename(filename) + ' (copy)')

        # all bands are "good" by default
        for bandNo in [1, 2, 3]:
            self.assertEqual(1, RasterReader(layer).badBandMultiplier(bandNo))
            self.assertEqual(1, RasterReader(layer2).badBandMultiplier(bandNo))

        # mark the first band as bad band
        qgsApp = start_app()
        initAll()
        enmapBox = EnMAPBox(None)
        enmapBox.onDataDropped([layer, layer2])
        panel = RasterLayerStylingApp.panel()
        panel.setUserVisible(True)
        panel.mLayer.setLayer(layer)
        panel.mGrayBand.mBandNo.setBand(1)
        panel.mGrayBand.mIsBadBand.setChecked(True)

        # first band is now "bad"
        self.assertEqual(0, RasterReader(layer).badBandMultiplier(1))
        self.assertEqual(0, RasterReader(layer2).badBandMultiplier(1))

        qgsApp.exec_()
