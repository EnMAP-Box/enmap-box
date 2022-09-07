from enmapboxprocessing.algorithm.randomsamplesfromregressiondatasetalgorithm import \
    RandomSamplesFromRegressionDatasetAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.utils import Utils
from testdata import regressor_multitarget_pkl


class TestRandomSamplesFromRegressionDatasetAlgorithm(TestCase):

    def test_multitarget(self):
        alg = RandomSamplesFromRegressionDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: regressor_multitarget_pkl,  # 6 targets, 2559 samples, 177 features
            alg.P_BINS: 10,
            alg.P_N: 1,
            alg.P_SEED: 42,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample2.pkl')
        }
        self.runalg(alg, parameters)

        dump = Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET])
        self.assertEqual((59, 177), Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET])['X'].shape)
        self.assertEqual((2500, 177), Utils.pickleLoad(parameters[alg.P_OUTPUT_COMPLEMENT])['X'].shape)
