import numpy as np

from enmapboxprocessing.algorithm.spectralindexoptimizeralgorithm import SpectralIndexOptimizerAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import regressionDatasetAsPkl


class TestSpectralIndexOptimizerAlgorithm(TestCase):

    def test(self):
        alg = SpectralIndexOptimizerAlgorithm()
        parameters = {
            alg.P_DATASET: regressionDatasetAsPkl,
            alg.P_MAX_FEATURES: 10,
            alg.P_OUTPUT_MATRIX: self.filename('scores.tif')
        }
        self.runalg(alg, parameters)
        array = np.array(RasterReader(parameters[alg.P_OUTPUT_MATRIX]).array())
        self.assertEqual((18, 10, 10), array.shape)

    def test_withFixedFeatures(self):
        alg = SpectralIndexOptimizerAlgorithm()
        parameters = {
            alg.P_DATASET: regressionDatasetAsPkl,
            alg.P_MAX_FEATURES: 10,
            alg.P_F1: 1,
            alg.P_F2: 1,
            alg.P_F3: 1,
            alg.P_FORMULAR: 'A+B-F1-F2-F3',
            alg.P_OUTPUT_MATRIX: self.filename('scores.tif')
        }
        self.runalg(alg, parameters)
