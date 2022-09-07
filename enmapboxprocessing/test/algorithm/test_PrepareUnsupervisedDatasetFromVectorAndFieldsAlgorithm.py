from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromvectorandfieldsalgorithm import \
    PrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from testdata import classificationDatasetAsVector


class TestPrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm(TestCase):

    def test(self):
        alg = PrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm()
        parameters = {
            alg.P_VECTOR: classificationDatasetAsVector,
            alg.P_FEATURE_FIELDS: [f'Sample__{i + 1}' for i in range(177)],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((299, 177), dump.X.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(parameters[alg.P_FEATURE_FIELDS], dump.features)
