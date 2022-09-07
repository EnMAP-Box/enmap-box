import numpy as np

from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcodealgorithm import \
    PrepareClassificationDatasetFromCodeAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump, Category
from enmapboxprocessing.utils import Utils


class TestPrepareClassificationDatasetFromCodeAlgorithm(TestCase):

    def test(self):
        alg = PrepareClassificationDatasetFromCodeAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CODE: alg.defaultCodeAsString(),
            alg.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        result = self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(result[alg.P_OUTPUT_DATASET]))
        self.assertEqual(
            [Category(value=1, name='class 1', color='#ff0000'), Category(value=2, name='class 2', color='#00ff00')],
            dump.categories
        )
        self.assertEqual(
            ['Feature 1', 'Feature 2', 'Feature 3'],
            dump.features
        )
        self.assertTrue(np.all(np.equal([[1, 2, 3], [4, 5, 6]], dump.X)))
        self.assertTrue(np.all(np.equal([[1], [2]], dump.y)))
