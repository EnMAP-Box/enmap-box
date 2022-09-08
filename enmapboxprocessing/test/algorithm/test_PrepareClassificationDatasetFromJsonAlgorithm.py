from enmapboxprocessing.algorithm.prepareclassificationdatasetfromjsonalgorithm import \
    PrepareClassificationDatasetFromJsonAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classificationDatasetAsJsonFile


class TestPrepareClassificationDatasetFromJsonAlgorithm(TestCase):

    def test(self):
        alg = PrepareClassificationDatasetFromJsonAlgorithm()
        parameters = {
            alg.P_JSON_FILE: classificationDatasetAsJsonFile,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual((58, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(5, len(dump.categories))
        self.assertIsNone(dump.classifier)
