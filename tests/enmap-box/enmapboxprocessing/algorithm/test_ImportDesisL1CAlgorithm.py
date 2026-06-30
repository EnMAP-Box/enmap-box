from osgeo import gdal

from enmapboxprocessing.algorithm.importdesisl1calgorithm import ImportDesisL1CAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import sensorProductsRoot, SensorProducts


class TestImportDesisL1CAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportDesisL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Desis.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('desisL1C.vrt'),
        }

        self.runalg(alg, parameters)

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportDesisL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Desis.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('desisL1C.tif'),
        }

        result = self.runalg(alg, parameters)
        ds: gdal.Dataset = gdal.Open(result[alg.P_OUTPUT_RASTER])
        driver: gdal.Driver = ds.GetDriver()
        self.assertEqual('GeoTIFF', driver.LongName)
