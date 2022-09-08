from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromjsonalgorithm import \
    PrepareUnsupervisedDatasetFromJsonAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import regressionDatasetAsJsonFile


class TestPrepareUnsupervisedDatasetFromJsonAlgorithm(TestCase):

    def test(self):
        alg = PrepareUnsupervisedDatasetFromJsonAlgorithm()
        parameters = {
            alg.P_JSON_FILE: regressionDatasetAsJsonFile,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((51, 177), dump.X.shape)
        self.assertEqual(177, len(dump.features))
        self.assertIsNone(dump.transformer)
