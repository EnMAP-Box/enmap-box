from os.path import exists

from enmapboxprocessing.algorithm.aggregateardrastersalgorithm import AggregateArdRastersAlgorithm
from enmapboxprocessing.algorithm.aggregaterasterbandsalgorithm import AggregateRasterBandsAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase


class TestArdAggregateRastersAlgorithm(TestCase):

    def test(self):
        dataCube = r'D:\data\EnFireMap\cube'
        if not exists(dataCube):
            return

        alg = AggregateArdRastersAlgorithm()
        parameters = {
            alg.P_DATA_CUBE: dataCube,
            alg.P_BASENAME_FILTER: 'ENMAPL2A_*_SPECTRAL_IMAGE.TIF',
            alg.P_FUNCTION: [
                AggregateRasterBandsAlgorithm().MinimumFunction, AggregateRasterBandsAlgorithm().ArithmeticMeanFunction,
                AggregateRasterBandsAlgorithm().MaximumFunction
            ],
            alg.P_OUTPUT_BASENAME: 'aggregation.{function}.tif',  # write function-wise by using the {...} pattern
            alg.P_OUTPUT_DATA_CUBE: self.filename('dataCube')
        }
        self.runalg(alg, parameters)
