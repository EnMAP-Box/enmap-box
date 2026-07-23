from enmapboxprocessing.algorithm.classseparabilityalgorithm import ClassSeparabilityAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import classificationDatasetAsSkopsFile


class TestClassSeparabilityAlgorithm(TestCase):

    def test(self):
        alg = ClassSeparabilityAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classificationDatasetAsSkopsFile,
        }
        self.runalg(alg, parameters)
