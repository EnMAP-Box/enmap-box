import numpy as np

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase


class TestRasterMetadataEditor(TestCase):

    def setUp(self):
        self.filename = self.filename('raster.tif')
        self.raster = Driver(self.filename).createFromArray(np.zeros((3, 1, 1)))

    def reopen(self):
        uri = self.raster.source()
        del self.raster
        self.raster = RasterReader(uri)

    def test_setMeta_ReopenRaster_getMeta(self):
        self.raster.setMetadataItem('a', 1)
        self.raster.setMetadataItem('b', 2.3)
        self.raster.setMetadataItem('c', 'A')
        self.raster.setMetadataItem('d', [1, 2.3, 'A'])
        self.reopen()
        self.assertEqual(self.raster.metadataItem('a'), '1')
        self.assertEqual(self.raster.metadataItem('b'), '2.3')
        self.assertEqual(self.raster.metadataItem('c'), 'A')
        self.assertEqual(self.raster.metadataItem('d'), ['1', '2.3', 'A'])

    def test_setBandMeta_ReopenRaster_getBandMeta(self):
        self.raster.setMetadataItem('a', 1, bandNo=1)
        self.raster.setMetadataItem('b', 2.3, bandNo=1)
        self.raster.setMetadataItem('c', 'A', bandNo=1)
        self.raster.setMetadataItem('d', [1, 2.3, 'A'], bandNo=1)
        self.reopen()
        self.assertEqual(self.raster.metadataItem('a', bandNo=1), '1')
        self.assertEqual(self.raster.metadataItem('b', bandNo=1), '2.3')
        self.assertEqual(self.raster.metadataItem('c', bandNo=1), 'A')
        self.assertEqual(self.raster.metadataItem('d', bandNo=1), ['1', '2.3', 'A'])
