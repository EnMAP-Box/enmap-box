from enmapboxprocessing.algorithm.regressionperformancealgorithm import RegressionPerformanceAlgorithm

from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import fraction_map_l3, fraction_points

openReport = True


class TestRegressionPerformanceSimpleAlgorithm(TestCase):

    def test(self):
        alg = RegressionPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSION: fraction_map_l3,
            alg.P_REFERENCE: fraction_points,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def test_perfectMap(self):
        alg = RegressionPerformanceAlgorithm()
        parameters = {
            alg.P_REGRESSION: fraction_map_l3,
            alg.P_REFERENCE: fraction_map_l3,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)
