from enmapboxprocessing.algorithm.mergeclassificationdatasetalgorithm import MergeClassificationDatasetsAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classifierDumpPkl


class TestMergeClassificationDatasetsAlgorithm(TestCase):

    def test_fitted(self):
        alg = MergeClassificationDatasetsAlgorithm()
        parameters = {
            alg.P_DATASETS: [classifierDumpPkl, classifierDumpPkl],
            alg.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((116, 177), dump.X.shape)
        self.assertEqual((116, 1), dump.y.shape)
