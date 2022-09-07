from enmapboxprocessing.algorithm.regressorperformancealgorithm import RegressorPerformanceAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import regressor_pkl, regressor_singletarget_pkl

openReport = True


class TestRegressorPerformanceAlgorithm(TestCase):

    def test_trainPerformance_multiTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressor_pkl,
            alg.P_DATASET: regressor_pkl,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance_multiTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressor_pkl,
            alg.P_DATASET: regressor_pkl,
            alg.P_NFOLD: 3,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_trainPerformance_singleTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressor_singletarget_pkl,
            alg.P_DATASET: regressor_singletarget_pkl,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance_singleTarget(self):
        alg = RegressorPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressor_singletarget_pkl,
            alg.P_DATASET: regressor_singletarget_pkl,
            alg.P_NFOLD: 10,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually
