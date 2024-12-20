from enmapboxprocessing.algorithm.selectfeaturesfromdatasetalgorithm import SelectFeaturesFromDatasetAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classifierDumpPkl


class TestSelectFeaturesFromDatasetAlgorithm(TestCase):

    def test(self):
        alg = SelectFeaturesFromDatasetAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_FEATURE_LIST: "1, 'band 18 (0.508000 Micrometers)', 177",
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 3), dump.X.shape)
        self.assertListEqual(
            ['band 8 (0.460000 Micrometers)', 'band 18 (0.508000 Micrometers)', 'band 239 (2.409000 Micrometers)'],
            dump.features
        )
