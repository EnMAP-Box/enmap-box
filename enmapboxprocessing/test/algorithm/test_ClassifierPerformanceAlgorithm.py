from enmapboxprocessing.algorithm.classifierperformancealgorithm import ClassifierPerformanceAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import classifierDumpPkl


class TestClassifierPerformanceAlgorithm(TestCase):

    def test_trainPerformance(self):
        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifierDumpPkl,
            alg.P_DATASET: classifierDumpPkl,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance(self):
        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifierDumpPkl,
            alg.P_DATASET: classifierDumpPkl,
            alg.P_NFOLD: 3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually
