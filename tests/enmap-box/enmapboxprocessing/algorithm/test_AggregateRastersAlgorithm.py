from os.path import join, exists

from enmapboxprocessing.algorithm.aggregaterasterbandsalgorithm import AggregateRasterBandsAlgorithm
from enmapboxprocessing.algorithm.aggregaterastersalgorithm import AggregateRastersAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader


class TestAggregateRastersAlgorithm(TestCase):

    def test(self):
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
            alg.P_OUTPUT_BASENAME: 'aggregation.tif',
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

    def test_realData(self):
        root = r'D:\data\EnFireMap\cube\X0005_Y0012'
        if not exists(root):
            return

        rasters = [
            join(root, 'ENMAPL2A_230302_SPECTRAL_IMAGE.TIF'),
            join(root, 'ENMAPL2A_230310_SPECTRAL_IMAGE.TIF')
        ]

        alg = AggregateRastersAlgorithm()
        parameters = {
            alg.P_RASTERS: rasters,
            alg.P_FUNCTION: [
                AggregateRasterBandsAlgorithm().MinimumFunction, AggregateRasterBandsAlgorithm().ArithmeticMeanFunction,
                AggregateRasterBandsAlgorithm().MaximumFunction
            ],
            alg.P_OUTPUT_BASENAME: 'aggregation.tif',
            alg.P_OUTPUT_FOLDER: self.createTestOutputFolder()
        }
        self.runalg(alg, parameters)
