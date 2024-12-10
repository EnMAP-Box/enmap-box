from enmapboxprocessing.algorithm.importlandsatl2algorithm import ImportLandsatL2Algorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportLandsatL2Algorithm(TestCase):

    def test_L9_C2(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Landsat.LC09_L2_MtlTxt,
            alg.P_OUTPUT_RASTER: self.filename('landsat9L2C2.vrt')
        }

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        # self.assertEqual(25984874883, round(np.sum(array, dtype=float)))

    def test_L8_C2(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Landsat.LC08_L2_MtlTxt,
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2.vrt')
        }

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        # self.assertEqual(25984874883, round(np.sum(array, dtype=float)))

    def test_L7_C2(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Landsat.LE07_L2_MtlTxt,
            alg.P_OUTPUT_RASTER: self.filename('landsat7L2C2.vrt')
        }

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        # self.assertEqual(14003330657, round(np.sum(array, dtype=float)))

    def test_L5_C2(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Landsat.LT05_L2_MtlTxt,
            alg.P_OUTPUT_RASTER: self.filename('landsat5L2C2.vrt')
        }

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        # self.assertEqual(31240899446, round(np.sum(array, dtype=float)))

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Landsat.LC09_L2_MtlTxt,
            alg.P_OUTPUT_RASTER: self.filename('landsat9L2C2.tif')
        }

        result = self.runalg(alg, parameters)
