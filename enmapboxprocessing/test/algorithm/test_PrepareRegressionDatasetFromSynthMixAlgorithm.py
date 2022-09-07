from os.path import join

from enmapboxprocessing.algorithm.prepareregressiondatasetfromsynthmixalgorithm import \
    PrepareRegressionDatasetFromSynthMixAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump, RegressorDump
from enmapboxprocessing.utils import Utils
from testdata import (classifier_pkl)


class TestFitClassifierAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromSynthMixAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_N: 10,
            alg.P_INCLUDE_ENDMEMBER: False,
            alg.P_OUTPUT_FOLDER: self.filename('synthmix')
        }
        self.runalg(alg, parameters)
        for category in ClassifierDump.fromDict(Utils.pickleLoad(classifier_pkl)).categories:
            filename = join(parameters[alg.P_OUTPUT_FOLDER], category.name + '.pkl')
            dump = RegressorDump.fromDict(Utils.pickleLoad(filename))
            self.assertEqual(1, len(dump.targets))
            self.assertEqual(category.name, dump.targets[0].name)
            self.assertEqual(category.color, dump.targets[0].color)
            self.assertEqual((10, 177), dump.X.shape)
            self.assertEqual((10, 1), dump.y.shape)
