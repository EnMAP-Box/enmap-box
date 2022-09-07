from enmapboxprocessing.algorithm.classifierfeaturerankingpermutationimportancealgorithm import \
    ClassifierFeatureRankingPermutationImportanceAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import (classifier_pkl)


class TestClassifierPerformanceAlgorithm(TestCase):

    def test(self):
        alg = ClassifierFeatureRankingPermutationImportanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifier_pkl,
            alg.P_OPEN_REPORT: False,
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)
