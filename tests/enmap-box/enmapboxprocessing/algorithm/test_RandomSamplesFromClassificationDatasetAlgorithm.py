from enmapboxprocessing.algorithm.randomsamplesfromclassificationdatasetalgorithm import \
    RandomSamplesFromClassificationDatasetAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classifierDumpSkops


class TestRandomSamplesFromClassificationDatasetAlgorithm(TestCase):

    def test_N(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpSkops,
            alg.P_N: 10,
            alg.P_OUTPUT_DATASET: self.filename('sample.skops'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample2.skops')
        }
        self.runalg(alg, parameters)
        self.assertEqual(48, len(Utils.modelLoad(parameters[alg.P_OUTPUT_DATASET])['X']))
        self.assertEqual(10, len(Utils.modelLoad(parameters[alg.P_OUTPUT_COMPLEMENT])['X']))

    def test_N_asList(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpSkops,
            alg.P_N: str([3]),
            alg.P_OUTPUT_DATASET: self.filename('sample.skops'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample2.skops')
        }
        self.runalg(alg, parameters)
        self.assertEqual(3 * 5, len(Utils.modelLoad(parameters[alg.P_OUTPUT_DATASET])['X']))

    def test_N_withReplacemant(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpSkops,
            alg.P_N: 100,
            alg.P_REPLACE: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.skops'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample2.skops')
        }
        self.runalg(alg, parameters)
        self.assertEqual(500, len(Utils.modelLoad(parameters[alg.P_OUTPUT_DATASET])['X']))

    def test_P(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpSkops,
            alg.P_N: 10,
            alg.P_PROPORTIONAL: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.skops'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample_complement.skops')
        }
        self.runalg(alg, parameters)
        self.assertEqual(6, len(Utils.modelLoad(parameters[alg.P_OUTPUT_DATASET])['X']))
