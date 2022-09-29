from enmapboxprocessing.algorithm.prepareregressiondatasetfromfilesalgorithm import \
    PrepareRegressionDatasetFromFilesAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classificationDatasetAsForceFile


class TestPrepareRegressionDatasetFromFilesAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromFilesAlgorithm()
        parameters = {
            alg.P_FEATURE_FILE: classificationDatasetAsForceFile[0],
            alg.P_VALUE_FILE: classificationDatasetAsForceFile[1],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((15000, 20), dump.X.shape)
        self.assertEqual((15000, 1), dump.y.shape)
        self.assertEqual(20, len(dump.features))
        self.assertEqual(1, len(dump.targets))
        self.assertEqual(['feature 1', 'feature 2'], dump.features[:2])
        self.assertListEqual(['variable 1'], [t.name for t in dump.targets])
