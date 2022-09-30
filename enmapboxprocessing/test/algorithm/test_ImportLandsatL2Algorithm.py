import numpy as np

from enmapboxprocessing.algorithm.importlandsatl2algorithm import ImportLandsatL2Algorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportLandsatL2Algorithm(TestCase):

    def test_L9_C1(self):
        pass  # Lansat 9 is not available in Collection 1 format (I guess)

    def test_L9_C2(self):
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LC09_L2SP_001053_20220215_20220217_02_T1\LC09_L2SP_001053_20220215_20220217_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat9L2C2.vrt')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        self.assertEqual(25984874883, round(np.sum(array, dtype=float)))

    def test_L8_C1(self):
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C1L2\LC080140322019033001T1-SC20190517105817\LC08_L1TP_014032_20190330_20190404_01_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C1.vrt')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        self.assertEqual(-139807431228.0, np.sum(array, dtype=float))

    def test_L8_C2(self):
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LC08_L2SP_192023_20210724_20210730_02_T1\LC08_L2SP_192023_20210724_20210730_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2.vrt')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        self.assertEqual(25984874883, round(np.sum(array, dtype=float)))

    def test_L7_C1(self):
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C1L2\LE070130322019031501T1-SC20190517110511\LE07_L1TP_013032_20190315_20190410_01_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat7L2C1.vrt')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        self.assertEqual(-34939854393.0, np.sum(array, dtype=float))

    def test_L7_C2(self):
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LE07_L2SP_193023_20210605_20210701_02_T1\LE07_L2SP_193023_20210605_20210701_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat7L2C2.vrt')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        self.assertEqual(14003330657, round(np.sum(array, dtype=float)))

    def test_L5_C1(self):
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C1L2\LT050130322011062101T1-SC20190517110232\LT05_L1TP_013032_20110621_20160831_01_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat5L2C1.vrt')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return
        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        self.assertEqual(199183395583.0, np.sum(array, dtype=float))

    def test_L5_C2(self):
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LT05_L2SP_192024_20111102_20200820_02_T1\LT05_L2SP_192024_20111102_20200820_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat5L2C2.vrt')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        array = RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])
        self.assertEqual(31240899446, round(np.sum(array, dtype=float)))
