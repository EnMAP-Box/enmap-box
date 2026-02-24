import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportEnmapL2AAlgorithm(TestCase):

    def test_excludeNoDataBands(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_EXCLUDE_NO_DATA_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_withoutNoDataBands.vrt'),
        }
        result = self.runalg(alg, parameters)

        self.assertEqual(RasterReader(result[alg.P_OUTPUT_RASTER]).bandCount(), 190)
        self.assertAlmostEqual(
            -11535788939.969,
            np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float), 3
        )

    def test_withNoDataBands(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_EXCLUDE_NO_DATA_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_withNoDataBands.vrt'),
        }
        result = self.runalg(alg, parameters)

        self.assertEqual(RasterReader(result[alg.P_OUTPUT_RASTER]).bandCount(), 212)
        self.assertAlmostEqual(
            -11535788939.969,
            np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float), 3
        )

    def test_OrderByDetectorOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.OrderByDetectorOverlapOption,
            alg.P_EXCLUDE_NO_DATA_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_OrderByWavelength.vrt'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(224, RasterReader(result[alg.P_OUTPUT_RASTER]).bandCount())

    def test_OrderByWavelengthOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.OrderByWavelengthOverlapOption,
            alg.P_EXCLUDE_NO_DATA_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_OrderByWavelength.vrt'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(224, RasterReader(result[alg.P_OUTPUT_RASTER]).bandCount())

    def test_VnirOnlyOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.VnirOnlyOverlapOption,
            alg.P_EXCLUDE_NO_DATA_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_VnirOnly.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(214, reader.bandCount())

    def test_SwirOnlyOverlapOption(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_DETECTOR_OVERLAP: alg.SwirOnlyOverlapOption,
            alg.P_EXCLUDE_NO_DATA_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_SwirOnly.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(212, reader.bandCount())

    def test_ardProduct(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_ARD_MetadataXml,
            alg.P_EXCLUDE_NO_DATA_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_ARD.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A.tif'),
        }
        result = self.runalg(alg, parameters)
        ds: gdal.Dataset = gdal.Open(result[alg.P_OUTPUT_RASTER])
        driver: gdal.Driver = ds.GetDriver()
        self.assertEqual('GeoTIFF', driver.LongName)

    def test_zip(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L2A_Zip,
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A_fromZip.vrt'),
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(190, reader.bandCount())
