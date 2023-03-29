from enmapboxprocessing.algorithm.regressionperformancealgorithm import RegressionPerformanceAlgorithm

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import fraction_map_l3, fraction_point_multitarget


class TestRegressionPerformanceSimpleAlgorithm(TestCase):

    def test(self):
        alg = RegressionPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSION: fraction_map_l3,
            alg.P_REFERENCE: fraction_point_multitarget,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def test_perfectMap(self):
        alg = RegressionPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSION: fraction_map_l3,
            alg.P_REFERENCE: fraction_map_l3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)
