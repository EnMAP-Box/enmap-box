from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedvectorandfieldsalgorithm import \
    PrepareClassificationDatasetFromCategorizedVectorAndFieldsAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classificationDatasetAsCsvVector


class TestPrepareClassificationDatasetFromVectorAndFieldsAlgorithm(TestCase):

    def test(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAndFieldsAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: classificationDatasetAsCsvVector,
            alg.P_FEATURE_FIELDS: [f'Sample__{i + 1}' for i in range(177)],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((299, 177), dump.X.shape)
        self.assertEqual((299, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(parameters[alg.P_FEATURE_FIELDS], dump.features)
        self.assertListEqual([1, 2, 3, 4, 5], [c.value for c in dump.categories])
        self.assertListEqual(
            ['impervious', 'low vegetation', 'tree', 'soil', 'water'], [c.name for c in dump.categories]
        )
