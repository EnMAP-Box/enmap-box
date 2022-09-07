from enmapboxprocessing.algorithm.prepareclassificationdatasetfromfilesalgorithm import \
    PrepareClassificationDatasetFromFilesAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from testdata import classificationSampleAsCsv


class TestPrepareClassificationDatasetFromFilesAlgorithm(TestCase):

    def test(self):
        alg = PrepareClassificationDatasetFromFilesAlgorithm()
        parameters = {
            alg.P_FEATURE_FILE: classificationSampleAsCsv[0],
            alg.P_VALUE_FILE: classificationSampleAsCsv[1],
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((15000, 20), dump.X.shape)
        self.assertEqual((15000, 1), dump.y.shape)
        self.assertEqual(20, len(dump.features))
        self.assertEqual(6, len(dump.categories))
        self.assertEqual(['feature 1', 'feature 2'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4, 5, 6], [c.value for c in dump.categories])
        self.assertListEqual(['1', '2', '3', '4', '5', '6'], [c.name for c in dump.categories])
