from testdata import (classifier_pkl)
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.mergeclassificationdatasetalgorithm import MergeClassificationDatasetsAlgorithm

class TestMergeClassificationDatasetsAlgorithm(TestCase):

    def test_fitted(self):
        alg = MergeClassificationDatasetsAlgorithm()
        parameters = {
            alg.P_DATASETS: [classifier_pkl, classifier_pkl],
            alg.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((116, 177), dump.X.shape)
        self.assertEqual((116, 1), dump.y.shape)
