from osgeo import gdal

from enmapboxprocessing.algorithm.importdesisl2aalgorithm import ImportDesisL2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import sensorProductsRoot, SensorProducts


class TestImportDesisL2AAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportDesisL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Desis.L2A_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('desisL2A.vrt'),
        }

        result = self.runalg(alg, parameters)

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportDesisL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Desis.L2A_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('desisL2A.tif'),
        }

        result = self.runalg(alg, parameters)
        ds: gdal.Dataset = gdal.Open(result[alg.P_OUTPUT_RASTER])
        driver: gdal.Driver = ds.GetDriver()
        self.assertEqual('GeoTIFF', driver.LongName)
