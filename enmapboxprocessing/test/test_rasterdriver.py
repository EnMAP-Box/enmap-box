import numpy as np
from osgeo import gdal

from enmapbox.exampledata import enmap
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase
from qgis.core import QgsCoordinateReferenceSystem, Qgis, QgsRasterLayer


class TestDriver(TestCase):

    def test_enmap(self):
        ds = gdal.Open(enmap)
        array = ds.ReadAsArray()
        layer = QgsRasterLayer(enmap)
        outraster = Driver(self.filename('enmap.tif')).createFromArray(array, extent=layer.extent(), crs=layer.crs())
        outraster.setNoDataValue(-99)
        outraster.setMetadataItem('a', 42)

    def test_createSinglePixel_3Band_PseudoRaster(self):
        shape = (3, 1, 1)
        array = np.array(list(range(np.product(shape)))).reshape(shape)
        array[:, 0, 0] = -1
        filename = self.filename('raster.bsq')
        Driver(filename).createFromArray(array)
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
            Driver(filename).createFromArray(array)
            raster = RasterReader(filename)
            self.assertEqual(raster.array()[0].dtype, array.dtype)

    def test_createRaster_withDifferentFormats(self):
        for format in ['ENVI', 'GTiff']:
            filename = self.filename(f'raster_{format}.tif')
            array = np.array([[[1]], [[2]], [[3]]])
            Driver(filename, format=format).createFromArray(array)
            raster = RasterReader(filename)
            lead = raster.array()
            self.assertEqual(lead[0].dtype, array.dtype)
            self.assertArrayEqual(lead, array)

    def test_createRaster_likeExistingRaster(self):
        shape = 3, 5, 6
        filename1 = self.filename('raster1.tif')
        filename2 = self.filename('raster2.tif')
        Driver(filename1).createFromArray(np.zeros(shape))
        raster1 = RasterReader(filename1)
        Driver(self.filename('raster2.tif')).createLike(raster1)
        raster2 = RasterReader(filename2)
        self.assertEqual(raster1.extent(), raster2.extent())
        self.assertEqual(raster1.width(), raster2.width())
        self.assertEqual(raster1.height(), raster2.height())
        self.assertEqual(raster1.bandCount(), raster2.bandCount())

    def test_createRaster_likeExistingRaster_butDifferentBandCount_andDataType(self):
        shape = 3, 5, 6
        filename1 = self.filename('raster1.tif')
        filename2 = self.filename('raster2.tif')
        Driver(filename1).createFromArray(np.zeros(shape))
        Driver(filename2).createLike(RasterReader(filename1), nBands=1, dataType=Qgis.Byte)
        raster2 = RasterReader(filename2)
        self.assertEqual(1, raster2.bandCount())
        self.assertEqual(Qgis.Byte, raster2.dataType(1))
