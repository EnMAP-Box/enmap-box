import numpy as np
from osgeo import gdal

from enmapboxtestdata import enmap

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.testcase import TestCase
from qgis.core import QgsCoordinateReferenceSystem, Qgis, QgsRasterLayer


class TestDriver(TestCase):

    def test_enmap(self):
        ds = gdal.Open(enmap)
        array = ds.ReadAsArray()
        layer = QgsRasterLayer(enmap)
        writer = Driver(self.filename('enmap.tif')).createFromArray(array, extent=layer.extent(), crs=layer.crs())
        writer.setNoDataValue(-99)
        writer.setMetadataItem('a', 42)
        writer.close()

    def test_createSinglePixel_3Band_PseudoRaster(self):
        shape = (3, 1, 1)
        array = np.array(list(range(np.prod(shape)))).reshape(shape)
        array[:, 0, 0] = -1
        filename = self.filename('raster.bsq')
        writer = Driver(filename).createFromArray(array)
        writer.close()
        raster = RasterReader(filename)

        crs: QgsCoordinateReferenceSystem = raster.crs()
        self.assertFalse(crs == QgsCoordinateReferenceSystem.fromEpsgId(4326))
        self.assertEqual(1, raster.width())
        self.assertEqual(1, raster.height())
        self.assertEqual(3, raster.bandCount())
        self.assertArrayEqual(raster.array(), array)

    def test_createRaster_withDifferentDataTypes(self):
        for i, dtype in enumerate([np.uint8, np.float32, np.float64, np.int16, np.int32, np.uint16, np.uint32]):
            filename = self.filename(f'raster_{i}.tif')
            array = np.array([[[0]]], dtype=dtype)
            writer = Driver(filename).createFromArray(array)
            writer.close()
            raster = RasterReader(filename)
            self.assertEqual(raster.array()[0].dtype, array.dtype)

    def test_createRaster_withDifferentFormats(self):
        for format in ['ENVI', 'GTiff']:
            filename = self.filename(f'raster_{format}.tif')
            array = np.array([[[1]], [[2]], [[3]]])
            writer = Driver(filename, format=format).createFromArray(array)
            writer.close()
            raster = RasterReader(filename)
            lead = raster.array()
            self.assertArrayEqual(lead, array)

    def test_createRaster_likeExistingRaster(self):
        shape = 3, 5, 6
        filename1 = self.filename('raster1.tif')
        filename2 = self.filename('raster2.tif')
        writer = Driver(filename1).createFromArray(np.zeros(shape))
        writer.close()
        raster1 = RasterReader(filename1)
        writer = Driver(self.filename('raster2.tif')).createLike(raster1)
        writer.close()
        raster2 = RasterReader(filename2)
        self.assertEqual(raster1.extent(), raster2.extent())
        self.assertEqual(raster1.width(), raster2.width())
        self.assertEqual(raster1.height(), raster2.height())
        self.assertEqual(raster1.bandCount(), raster2.bandCount())

    def test_createRaster_likeExistingRaster_butDifferentBandCount_andDataType(self):
        shape = 3, 5, 6
        filename1 = self.filename('raster1.tif')
        filename2 = self.filename('raster2.tif')
        writer = Driver(filename1).createFromArray(np.zeros(shape))
        writer.close()
        writer = Driver(filename2).createLike(RasterReader(filename1), nBands=1, dataType=Qgis.DataType.Byte)
        writer.close()
        raster2 = RasterReader(filename2)
        self.assertEqual(1, raster2.bandCount())
        self.assertEqual(Qgis.DataType.Byte, raster2.dataType(1))

    def test_createArray_cutOverlap(self):
        array = np.ones((3, 15, 15))
        filename = self.filename('raster.bsq')
        writer = Driver(filename).createFromArray(array, overlap=5)
        writer.close()
        raster = RasterReader(filename)
        self.assertEqual(5, raster.width())
        self.assertEqual(5, raster.height())
        self.assertEqual(3, raster.bandCount())

    def test_defaultFormat(self):
        self.assertEqual('GTiff', Driver.formatFromExtension('.tif'))
        self.assertEqual('VRT', Driver.formatFromExtension('.vrt'))
        self.assertEqual('ENVI', Driver.formatFromExtension('.bsq'))
        self.assertEqual('ENVI', Driver.formatFromExtension('.bil'))
        self.assertEqual('ENVI', Driver.formatFromExtension('.bip'))
