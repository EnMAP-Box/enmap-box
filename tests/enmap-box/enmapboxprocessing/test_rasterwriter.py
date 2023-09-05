import numpy as np
from osgeo import gdal

from enmapboxtestdata import enmap
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.testcase import TestCase


class TestRasterWriter(TestCase):

    def test_init(self):
        ds = gdal.Open(enmap)
        writer = RasterWriter(ds)
        self.assertEqual(enmap, writer.source())

    def test_writeArray_all(self):
        writer = self.rasterFromValue((3, 5, 5), 0)
        writer.writeArray(np.ones((3, 5, 5)))
        writer.close()
        reader = RasterReader(writer.source())
        self.assertArrayEqual(1, reader.array())

    def test_writeArray_bandsList(self):
        writer = self.rasterFromValue((3, 5, 5), 0)
        writer.writeArray(np.ones((1, 5, 5)), bandList=[2])
        writer.close()
        reader = RasterReader(writer.source())
        self.assertArrayEqual(0, reader.array(bandList=[1, 3]))
        self.assertArrayEqual(1, reader.array(bandList=[2]))

    def test_writeArray_withOffset(self):
        writer = self.rasterFromValue((1, 5, 5), 0)
        writer.writeArray(np.ones((1, 3, 3)), xOffset=1, yOffset=1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertArrayEqual(1, reader.arrayFromPixelOffsetAndSize(1, 1, 3, 3))
        self.assertEqual(9, np.sum(reader.array()))

    def test_writeArray_withOverlap(self):
        writer = self.rasterFromValue((1, 5, 5), 0)
        writer.writeArray(np.ones((1, 7, 7)), overlap=1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertArrayEqual(1, reader.array())

    def test_fill_singleBand(self):
        writer = self.rasterFromValue((3, 5, 5), 0)
        writer.fill(1, 2)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertArrayEqual(0, reader.array(bandList=[1, 3]))
        self.assertArrayEqual(1, reader.array(bandList=[2]))

    def test_setNoDataValue_global(self):
        writer = self.rasterFromValue((2, 5, 5), 0)
        writer.setNoDataValue(-99)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(-99, reader.noDataValue(1))
        self.assertEqual(-99, reader.noDataValue(2))

    def test_setNoDataValue_individual(self):
        writer = self.rasterFromValue((3, 5, 5), 0)
        writer.close()  # need to close GeoTiff source and reopen to write to aux.xml
        ds = gdal.Open(writer.source())
        writer = RasterWriter(ds)
        writer.setNoDataValue(-111, 1)
        writer.setNoDataValue(-222, 2)
        writer.close()
        del ds

        reader = RasterReader(writer.source())
        self.assertEqual(-111, reader.noDataValue(1))
        self.assertEqual(-222, reader.noDataValue(2))
        self.assertIsNone(reader.noDataValue(3))

    def test_deleteNoDataValue_individual(self):
        writer = self.rasterFromValue((2, 5, 5), 0)
        writer.close()  # need to close GeoTiff source and reopen to write to aux.xml
        ds = gdal.Open(writer.source())
        writer = RasterWriter(ds)
        writer.setNoDataValue(-99)
        writer.deleteNoDataValue(2)
        writer.close()
        del ds
        reader = RasterReader(writer.source())
        self.assertEqual(-99, reader.noDataValue(1))
        self.assertIsNone(reader.noDataValue(2))

    def test_setOffset(self):
        writer = self.rasterFromValue((2, 5, 5), 0)
        writer.setOffset(42, 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(42, reader.offset(1))
        self.assertIsNone(reader.offset(2))

    def test_setScale(self):
        writer = self.rasterFromValue((2, 5, 5), 0)
        writer.setScale(42, 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(42, reader.scale(1))
        self.assertIsNone(reader.scale(2))

    def test_setMetadataItem(self):
        writer = self.rasterFromValue((1, 5, 5), 0)
        writer.setMetadataItem('key1', 1, '')
        writer.setMetadataItem('key2', 2, '', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual('1', reader.metadataItem('key1', ''))
        self.assertEqual('2', reader.metadataItem('key2', '', 1))

    def test_setMetadataDomain(self):
        writer = self.rasterFromValue((1, 5, 5), 0)
        writer.setMetadataDomain({'key1': 1}, '')
        writer.setMetadataItem('key2', 2, '', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual('1', reader.metadataItem('key1', ''))
        self.assertEqual('2', reader.metadataItem('key2', '', 1))
