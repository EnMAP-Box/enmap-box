from enmapboxprocessing.algorithm.regressorperformancealgorithm import RegressorPerformanceAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import regressorDumpPkl, regressorDumpSingleTargetPkl

openReport = True


class TestRegressorPerformanceAlgorithm(TestCase):

    def test_trainPerformance_multiTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpPkl,
            alg.P_DATASET: regressorDumpPkl,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance_multiTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpPkl,
            alg.P_DATASET: regressorDumpPkl,
            alg.P_NFOLD: 3,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_trainPerformance_singleTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpSingleTargetPkl,
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance_singleTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpSingleTargetPkl,
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_NFOLD: 10,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually
