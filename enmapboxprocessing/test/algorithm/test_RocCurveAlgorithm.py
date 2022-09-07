from enmapbox.exampledata import landcover_polygons
from enmapboxprocessing.algorithm.roccurvealgorithm import RocCurveAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import fraction_map_l3_tif, fraction_polygons_l3_tif, landcover_berlin_polygon_3classes_gpkg

openReport = True


class TestRocCurveAlgorithm(TestCase):

    def test(self):
        alg = RocCurveAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_PROBABILITY: fraction_map_l3_tif,
            alg.P_REFERENCE: landcover_polygons,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html'),
        }
        self.runalg(alg, parameters)

    def test_perfectMap(self):
        alg = RocCurveAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_PROBABILITY: fraction_polygons_l3_tif,
            alg.P_REFERENCE: landcover_berlin_polygon_3classes_gpkg,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_perfectMap.html'),
        }
        self.runalg(alg, parameters)
