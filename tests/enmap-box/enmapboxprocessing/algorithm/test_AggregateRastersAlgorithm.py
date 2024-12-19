from os.path import join

import numpy as np

from enmapboxprocessing.algorithm.aggregaterasterbandsalgorithm import AggregateRasterBandsAlgorithm
from enmapboxprocessing.algorithm.aggregaterastersalgorithm import AggregateRastersAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader


class TestAggregateRastersAlgorithm(TestCase):

    def test_aggregateBandWise_and_writeFunctionWise(self):
        writer1 = self.rasterFromValue((3, 1, 1), 1)
        writer1.setBandName('A', 1)
        writer1.setBandName('B', 2)
        writer1.setBandName('C', 3)
        writer1.close()
        writer2 = self.rasterFromValue((3, 1, 1), 2)
        writer2.close()
        writer3 = self.rasterFromValue((3, 1, 1), 3)
        writer3.close()
        rasters = [writer1.source(), writer2.source(), writer3.source()]
        alg = AggregateRastersAlgorithm()
        parameters = {
            alg.P_RASTERS: rasters,
            alg.P_FUNCTION: [
                AggregateRasterBandsAlgorithm().MinimumFunction, AggregateRasterBandsAlgorithm().ArithmeticMeanFunction,
                AggregateRasterBandsAlgorithm().MaximumFunction
            ],
            alg.P_OUTPUT_BASENAME: 'aggregation.{function}.tif',  # write function-wise by using the {...} pattern
            alg.P_OUTPUT_FOLDER: self.createTestOutputFolder()
        }
        self.runalg(alg, parameters)
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.minimum.tif'))
        self.assertEqual(1, reader.array()[0], [0, 0])
        self.assertEqual('A', reader.bandName(1))
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.arithmetic_mean.tif'))
        self.assertEqual(2, reader.array()[0], [0, 0])
        self.assertEqual('A', reader.bandName(1))
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.maximum.tif'))
        self.assertEqual(3, reader.array()[0], [0, 0])
        self.assertEqual('A', reader.bandName(1))

    def test_aggregateBandWise_and_notWriteFunctionWise(self):
        writer1 = self.rasterFromValue((3, 1, 1), 1)
        writer1.setBandName('A', 1)
        writer1.setBandName('B', 2)
        writer1.setBandName('C', 3)
        writer1.close()
        writer2 = self.rasterFromValue((3, 1, 1), 2)
        writer2.close()
        writer3 = self.rasterFromValue((3, 1, 1), 3)
        writer3.close()
        rasters = [writer1.source(), writer2.source(), writer3.source()]
        alg = AggregateRastersAlgorithm()
        parameters = {
            alg.P_RASTERS: rasters,
            alg.P_FUNCTION: [
                AggregateRasterBandsAlgorithm().MinimumFunction, AggregateRasterBandsAlgorithm().ArithmeticMeanFunction,
                AggregateRasterBandsAlgorithm().MaximumFunction
            ],
            alg.P_OUTPUT_BASENAME: 'aggregation.tif',  # write all in one file
            alg.P_OUTPUT_FOLDER: self.createTestOutputFolder()
        }
        self.runalg(alg, parameters)
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.tif'))
        self.assertListEqual([1, 2, 3] * 3, np.array(reader.array()).flatten().tolist())
        self.assertEqual('A - minimum', reader.bandName(1))
        self.assertEqual('A - arithmetic mean', reader.bandName(2))
        self.assertEqual('A - maximum', reader.bandName(3))
        self.assertEqual('B - minimum', reader.bandName(4))
        self.assertEqual('B - arithmetic mean', reader.bandName(5))
        self.assertEqual('B - maximum', reader.bandName(6))
        self.assertEqual('C - minimum', reader.bandName(7))
        self.assertEqual('C - arithmetic mean', reader.bandName(8))
        self.assertEqual('C - maximum', reader.bandName(9))

    def test_aggregateAllBands_writeFunctionWise(self):
        writer1 = self.rasterFromValue((3, 1, 1), 1)
        writer1.setBandName('A', 1)
        writer1.setBandName('B', 2)
        writer1.setBandName('C', 3)
        writer1.close()
        writer2 = self.rasterFromValue((3, 1, 1), 2)
        writer2.close()
        writer3 = self.rasterFromValue((3, 1, 1), 3)
        writer3.close()
        rasters = [writer1.source(), writer2.source(), writer3.source()]
        alg = AggregateRastersAlgorithm()
        parameters = {
            alg.P_RASTERS: rasters,
            alg.P_FUNCTION: [
                AggregateRasterBandsAlgorithm().MinimumFunction, AggregateRasterBandsAlgorithm().ArithmeticMeanFunction,
                AggregateRasterBandsAlgorithm().MaximumFunction
            ],
            alg.P_BANDWISE: False,
            alg.P_OUTPUT_BASENAME: 'aggregation.{function}.tif',  # write function-wise by using the {...} pattern
            alg.P_OUTPUT_FOLDER: self.createTestOutputFolder()
        }
        self.runalg(alg, parameters)
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.minimum.tif'))
        self.assertEqual(1, reader.bandCount())
        self.assertEqual(1, reader.array()[0], [0, 0])
        self.assertEqual('minimum', reader.bandName(1))
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.arithmetic_mean.tif'))
        self.assertEqual(1, reader.bandCount())
        self.assertEqual(2, reader.array()[0], [0, 0])
        self.assertEqual('arithmetic mean', reader.bandName(1))
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.maximum.tif'))
        self.assertEqual(1, reader.bandCount())
        self.assertEqual(3, reader.array()[0], [0, 0])
        self.assertEqual('maximum', reader.bandName(1))

    def test_aggregateAllBands_notWriteFunctionWise(self):
        writer1 = self.rasterFromValue((3, 1, 1), 1)
        writer1.setBandName('A', 1)
        writer1.setBandName('B', 2)
        writer1.setBandName('C', 3)
        writer1.close()
        writer2 = self.rasterFromValue((3, 1, 1), 2)
        writer2.close()
        writer3 = self.rasterFromValue((3, 1, 1), 3)
        writer3.close()
        rasters = [writer1.source(), writer2.source(), writer3.source()]
        alg = AggregateRastersAlgorithm()
        parameters = {
            alg.P_RASTERS: rasters,
            alg.P_FUNCTION: [
                AggregateRasterBandsAlgorithm().MinimumFunction, AggregateRasterBandsAlgorithm().ArithmeticMeanFunction,
                AggregateRasterBandsAlgorithm().MaximumFunction
            ],
            alg.P_BANDWISE: False,
            alg.P_OUTPUT_BASENAME: 'aggregation.tif',  # write all in one file
            alg.P_OUTPUT_FOLDER: self.createTestOutputFolder()
        }
        self.runalg(alg, parameters)
        reader = RasterReader(join(parameters[alg.P_OUTPUT_FOLDER], 'aggregation.tif'))
        self.assertEqual(3, reader.bandCount())
        self.assertListEqual([1, 2, 3], np.array(reader.array()).flatten().tolist())
        self.assertEqual('minimum', reader.bandName(1))
        self.assertEqual('arithmetic mean', reader.bandName(2))
        self.assertEqual('maximum', reader.bandName(3))
