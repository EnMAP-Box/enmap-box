from enmapboxprocessing.algorithm.prepareregressiondatasetfromjsonalgorithm import \
    PrepareRegressionDatasetFromJsonAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import regressionDatasetAsJsonFile


class TestPrepareRegressionDatasetFromJsonAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromJsonAlgorithm()
        parameters = {
            alg.P_JSON_FILE: regressionDatasetAsJsonFile,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((51, 177), dump.X.shape)
        self.assertEqual((51, 6), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(6, len(dump.targets))
        self.assertIsNone(dump.regressor)
