from enmapboxprocessing.algorithm.mergeclassificationdatasetalgorithm import MergeClassificationDatasetsAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classifierDumpSkops


class TestMergeClassificationDatasetsAlgorithm(TestCase):

    def test_fitted(self):
        alg = MergeClassificationDatasetsAlgorithm()
        parameters = {
            alg.P_DATASETS: [classifierDumpSkops, classifierDumpSkops],
            alg.P_OUTPUT_DATASET: self.filename('dataset.skops')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump.fromDict(Utils.modelLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((116, 177), dump.X.shape)
        self.assertEqual((116, 1), dump.y.shape)
