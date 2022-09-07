from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromfilealgorithm import \
    PrepareUnsupervisedDatasetFromFileAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from testdata import classificationSampleAsCsv


class TestPrepareUnsupervisedDatasetFromFileAlgorithm(TestCase):

    def test(self):
        alg = PrepareUnsupervisedDatasetFromFileAlgorithm()
        parameters = {
            alg.P_FEATURE_FILE: classificationSampleAsCsv[0],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((15000, 20), dump.X.shape)
        self.assertEqual(20, len(dump.features))
        self.assertEqual(['feature 1', 'feature 2'], dump.features[:2])
