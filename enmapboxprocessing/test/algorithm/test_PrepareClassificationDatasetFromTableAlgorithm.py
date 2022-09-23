from enmapboxprocessing.algorithm.prepareclassificationdatasetfromtablealgorithm import \
    PrepareClassificationDatasetFromTableAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classificationDatasetAsCsvVector


class TestPrepareClassificationDatasetFromTableAlgorithm(TestCase):

    def test_minimallySpecified_numberValues(self):
        alg = PrepareClassificationDatasetFromTableAlgorithm()
        parameters = {
            alg.P_TABLE: classificationDatasetAsCsvVector,
            alg.P_FEATURE_FIELDS: [f'Band_{i + 1}' for i in range(177)],
            alg.P_VALUE_FIELD: 'level_1_id',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual((58, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(parameters[alg.P_FEATURE_FIELDS], dump.features)
        self.assertEqual(['Band_1', 'Band_2'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4], [c.value for c in dump.categories])
        self.assertListEqual(['1', '2', '3', '4'], [c.name for c in dump.categories])

    def test_minimallySpecified_stringValues(self):
        alg = PrepareClassificationDatasetFromTableAlgorithm()
        parameters = {
            alg.P_TABLE: classificationDatasetAsCsvVector,
            alg.P_FEATURE_FIELDS: [f'Band_{i + 1}' for i in range(177)],
            alg.P_VALUE_FIELD: 'level_1',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual((58, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(parameters[alg.P_FEATURE_FIELDS], dump.features)
        self.assertEqual(['Band_1', 'Band_2'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4], [c.value for c in dump.categories])
        self.assertListEqual(['impervious', 'soil', 'vegetation', 'water'], [c.name for c in dump.categories])

    def test_fullySpecified(self):
        alg = PrepareClassificationDatasetFromTableAlgorithm()
        parameters = {
            alg.P_TABLE: classificationDatasetAsCsvVector,
            alg.P_FEATURE_FIELDS: [f'Band_{i + 1}' for i in range(177)],
            alg.P_VALUE_FIELD: 'level_1_id',
            alg.P_NAME_FIELD: 'level_1',
            alg.P_COLOR_FIELD: 'colors',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual((58, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(parameters[alg.P_FEATURE_FIELDS], dump.features)
        self.assertEqual(['Band_1', 'Band_2'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4], [c.value for c in dump.categories])
        self.assertListEqual(['impervious', 'vegetation', 'soil', 'water'], [c.name for c in dump.categories])
        self.assertListEqual(['#004242', '#00ff00', '#eeae02', '#0000ff'], [c.color for c in dump.categories])
