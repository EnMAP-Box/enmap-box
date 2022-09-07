import numpy as np

from enmapboxprocessing.algorithm.prepareregressiondatasetfromcodealgorithm import \
    PrepareRegressionDatasetFromCodeAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump, Target
from enmapboxprocessing.utils import Utils


class TestPrepareRegressionDatasetFromCodeAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromCodeAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CODE: alg.defaultCodeAsString(),
            alg.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        result = self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(result[alg.P_OUTPUT_DATASET]))
        self.assertEqual(
            [Target(name='variable 1', color='#ff0000'), Target(name='variable 2', color='#00ff00')],
            dump.targets
        )
        self.assertEqual(
            ['Feature 1', 'Feature 2', 'Feature 3'],
            dump.features
        )
        self.assertTrue(np.all(np.equal([[1, 2, 3], [4, 5, 6]], dump.X)))
        self.assertTrue(np.all(np.equal([[1.1, 1.2], [2.1, 2.2]], dump.y)))
