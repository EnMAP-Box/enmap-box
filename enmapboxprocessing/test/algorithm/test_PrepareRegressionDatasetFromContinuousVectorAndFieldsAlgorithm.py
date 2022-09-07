from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectorandfieldsalgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAndFieldsAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from testdata import classificationDatasetAsVector


class TestPrepareRegressionDatasetFromContinuousVectorAndFieldsAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromContinuousVectorAndFieldsAlgorithm()
        parameters = {
            alg.P_CONTINUOUS_VECTOR: classificationDatasetAsVector,
            alg.P_FEATURE_FIELDS: [f'Sample__{i + 1}' for i in range(177)],
            alg.P_TARGET_FIELDS: ['level_1_id', 'level_2_id', 'level_3_id'],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((299, 177), dump.X.shape)
        self.assertEqual((299, 3), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(parameters[alg.P_FEATURE_FIELDS], dump.features)
        self.assertListEqual([None] * 3, [c.color for c in dump.targets])
        self.assertListEqual(['level_1_id', 'level_2_id', 'level_3_id'], [t.name for t in dump.targets])
