from enmapboxprocessing.algorithm.classifierperformancealgorithm import ClassifierPerformanceAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import (classifier_pkl)


class TestClassifierPerformanceAlgorithm(TestCase):

    def test_trainPerformance(self):
        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifier_pkl,
            alg.P_DATASET: classifier_pkl,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance(self):
        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifier_pkl,
            alg.P_DATASET: classifier_pkl,
            alg.P_NFOLD: 3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually
