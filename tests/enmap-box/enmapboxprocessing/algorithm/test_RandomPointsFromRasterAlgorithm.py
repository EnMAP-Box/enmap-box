from enmapboxprocessing.algorithm.randompointsfromrasteralgorithm import RandomPointsFromRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap
from qgis.core import QgsVectorLayer


class TestRandomPointsFromRasterAlgorithm(TestCase):

    def test(self):
        alg = RandomPointsFromRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_BAND: 1,
            alg.P_N: [0, 100, 1,  # 0 points can be drawn from this range!
                      100, 200, 1,
                      200, 300, 1,
                      300, 500, 1,
                      500, 1000, 1],
            alg.P_DISTANCE_GLOBAL: 0,
            alg.P_DISTANCE_STRATUM: 0,
            alg.P_SEED: 42,
            alg.P_OUTPUT_POINTS: self.filename('points.gpkg')
        }
        self.runalg(alg, parameters)
        self.assertEqual(4, QgsVectorLayer(parameters[alg.P_OUTPUT_POINTS]).featureCount())
