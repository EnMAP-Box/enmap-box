from enmapboxprocessing.algorithm.randomsamplesfromclassificationdatasetalgorithm import \
    RandomSamplesFromClassificationDatasetAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.utils import Utils
from testdata import (classifier_pkl)


class TestRandomSamplesFromClassificationDatasetAlgorithm(TestCase):

    def test_N(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_N: 10,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample2.pkl')
        }
        self.runalg(alg, parameters)
        self.assertEqual(48, len(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET])['X']))
        self.assertEqual(10, len(Utils.pickleLoad(parameters[alg.P_OUTPUT_COMPLEMENT])['X']))

    def test_N_asList(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_N: str([3]),
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample2.pkl')
        }
        self.runalg(alg, parameters)
        self.assertEqual(3 * 5, len(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET])['X']))

    def test_N_withReplacemant(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_N: 100,
            alg.P_REPLACE: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample2.pkl')
        }
        self.runalg(alg, parameters)
        self.assertEqual(500, len(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET])['X']))

    def test_P(self):
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_N: 10,
            alg.P_PROPORTIONAL: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_COMPLEMENT: self.filename('sample_complement.pkl')
        }
        self.runalg(alg, parameters)
        self.assertEqual(6, len(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET])['X']))
