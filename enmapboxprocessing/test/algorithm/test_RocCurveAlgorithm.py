from enmapbox.exampledata import landcover_polygons
from enmapboxprocessing.algorithm.roccurvealgorithm import RocCurveAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import fraction_map_l3, fraction_polygons_l3, landcover_map_l3, landcover_polygons_3classes

openReport = True


class TestRocCurveAlgorithm(TestCase):

    def test(self):
        alg = RocCurveAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_PROBABILITY: fraction_map_l3,
            alg.P_REFERENCE: landcover_polygons,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def test_perfectMap(self):
        alg = RocCurveAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_PROBABILITY: fraction_polygons_l3,
            alg.P_REFERENCE: landcover_polygons_3classes,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_perfectMap.html'),
        }
        self.runalg(alg, parameters)
