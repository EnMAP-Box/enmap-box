import numpy as np

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.aggregaterasterbandsalgorithm import AggregateRasterBandsAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestAggregateRasterBandsAlgorithm(TestCase):

    def test_p0_and_p100(self):
        alg = AggregateRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FUNCTION: [alg.P0, alg.P0 + 100],
            alg.P_OUTPUT_RASTER: self.filename('aggregation_P0_P100.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertAlmostEqual(5669.0, np.max(array))

    def test_mean(self):
        alg = AggregateRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FUNCTION: [alg.ArithmeticMeanFunction],
            alg.P_OUTPUT_RASTER: self.filename('aggregation_Mean.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        array = reader.array()
        self.assertAlmostEqual(4388.7344, np.max(array), 4)

    def test_all(self):
        alg = AggregateRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_FUNCTION: list(range(len(alg.O_FUNCTION))),
            alg.P_OUTPUT_RASTER: self.filename('aggregation_All.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        array = reader.array()

    def test_issue1423(self):
        alg = AggregateRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: r'D:\data\issues\1423\BLUE.vrt',
            alg.P_FUNCTION: list(range(len(alg.O_FUNCTION))),
            alg.P_OUTPUT_RASTER: self.filename('aggregation_BLUE2.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        array = reader.array()

    def test_issue1424(self):
        alg = AggregateRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: r'D:\data\issues\1423\BLUE.vrt',
            alg.P_FUNCTION: [alg.SumFunction],
            alg.P_OUTPUT_RASTER: self.filename('aggregation_BLU1.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        array = reader.array()
