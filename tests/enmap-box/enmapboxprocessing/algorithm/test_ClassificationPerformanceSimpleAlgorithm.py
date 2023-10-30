from math import isnan

from tests.enmapboxtestdata import landcover_polygon
from enmapboxprocessing.algorithm.classificationperformancesimplealgorithm import \
    ClassificationPerformanceSimpleAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.utils import Utils
from tests.enmapboxtestdata import landcover_map_l3

writeToDisk = True


class TestClassificationPerformanceSimpleAlgorithm(TestCase):

    def test(self):
        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: landcover_map_l3,
            alg.P_REFERENCE: landcover_polygon,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def test_perfectMap(self):
        alg = ClassificationPerformanceSimpleAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFICATION: landcover_map_l3,
            alg.P_REFERENCE: landcover_map_l3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_perfectMap.html'),
        }
        result = self.runalg(alg, parameters)
        stats = Utils.jsonLoad(result[alg.P_OUTPUT_REPORT] + '.json')
        for v in stats['producers_accuracy_se'] + stats['users_accuracy_se']:
            self.assertFalse(isnan(v))  # previously we had NaN values, so better check this
