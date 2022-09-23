from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.randompointsfrommaskrasteralgorithm import RandomPointsFromMaskRasterAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.core import QgsRasterLayer


class TestRandomPointsInMaskAlgorithm(TestCase):

    def test(self):
        alg = RandomPointsFromMaskRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_MASK: QgsRasterLayer(enmap),
            alg.P_N: 100000000,
            alg.P_DISTANCE: 300,
            alg.P_SEED: 42,
            alg.P_OUTPUT_POINTS: self.filename('points.gpkg')
        }
        self.runalg(alg, parameters)
        # self.assertEqual(26317, QgsVectorLayer(parameters[alg.P_OUTPUT_VECTOR]).featureCount())
