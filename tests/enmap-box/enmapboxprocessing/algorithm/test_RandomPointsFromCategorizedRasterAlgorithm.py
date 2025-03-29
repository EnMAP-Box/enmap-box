import numpy as np

from enmapboxprocessing.algorithm.randompointsfromcategorizedrasteralgorithm import \
    RandomPointsFromCategorizedRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import landcover_map_l3
from qgis.core import QgsRasterLayer, QgsVectorLayer


class TestRandomPointsFromCategorizedRasterAlgorithm(TestCase):

    def test(self):
        alg = RandomPointsFromCategorizedRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_STRATIFICATION: QgsRasterLayer(landcover_map_l3),
            alg.P_N: 100000000,
            alg.P_DISTANCE_GLOBAL: 0,
            alg.P_DISTANCE_STRATUM: 45,
            alg.P_SEED: 42,
            alg.P_OUTPUT_POINTS: self.filename('points.gpkg')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(26317, QgsVectorLayer(parameters[alg.P_OUTPUT_POINTS]).featureCount())

    def test_kernel(self):
        self.assertTrue(np.all(np.equal([[0]], RandomPointsFromCategorizedRasterAlgorithm.makeKernel(30, 30, 0))))
        self.assertTrue(np.all(np.equal([[0]], RandomPointsFromCategorizedRasterAlgorithm.makeKernel(30, 30, 15))))
        self.assertTrue(np.all(np.equal(
            [[1, 1, 1], [1, 0, 1], [1, 1, 1]], RandomPointsFromCategorizedRasterAlgorithm.makeKernel(30, 30, 16)
        )))
        self.assertTrue(np.all(np.equal(
            [[1, 0, 1], [0, 0, 0], [1, 0, 1]], RandomPointsFromCategorizedRasterAlgorithm.makeKernel(30, 30, 30)
        )))
        self.assertTrue(np.all(np.equal(
            [[0, 0, 0], [0, 0, 0], [0, 0, 0]], RandomPointsFromCategorizedRasterAlgorithm.makeKernel(30, 30, 45)
        )))

    def _test_debug874(self):
        alg = RandomPointsFromCategorizedRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_STRATIFICATION: QgsRasterLayer(r'C:\Users\Andreas\Downloads\all_features_Cnv.tif'),
            alg.P_N: 1,
            alg.P_SEED: 42,
            alg.P_OUTPUT_POINTS: self.filename('points.gpkg')
        }
        result = self.runalg(alg, parameters)
