from enmapboxprocessing.algorithm.prepareregressiondatasetfromtablealgorithm import \
    PrepareRegressionDatasetFromTableAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from testdata import classificationDatasetAsCsv


class TestPrepareRegressionDatasetFromTableAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromTableAlgorithm()
        parameters = {
            alg.P_TABLE: classificationDatasetAsCsv,
            alg.P_FEATURE_FIELDS: [f'Band_{i + 1}' for i in range(177)],
            alg.P_TARGET_FIELDS: ['level_1_id', 'level_2_id'],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual((58, 2), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(parameters[alg.P_FEATURE_FIELDS], dump.features)
        self.assertEqual(['Band_1', 'Band_2'], dump.features[:2])
        self.assertListEqual(['level_1_id', 'level_2_id'], [t.name for t in dump.targets])
