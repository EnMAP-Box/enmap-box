import numpy as np

from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils


class TestPrepareUnsupervisedDatasetFromCodeAlgorithm(TestCase):

    def test(self):
        alg = PrepareUnsupervisedDatasetFromCodeAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CODE: alg.defaultCodeAsString(),
            alg.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        result = self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(result[alg.P_OUTPUT_DATASET]))
        self.assertEqual(
            ['Feature 1', 'Feature 2', 'Feature 3'],
            dump.features
        )
        self.assertTrue(np.all(np.equal([[1, 2, 3], [4, 5, 6]], dump.X)))
