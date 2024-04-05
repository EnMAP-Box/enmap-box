import numpy as np

from enmapboxprocessing.algorithm.prepareregressiondatasetfromfilesalgorithm import \
    PrepareRegressionDatasetFromFilesAlgorithm
from enmapboxprocessing.algorithm.spectralindexoptimizeralgorithm import SpectralIndexOptimizerAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import regressionDatasetAsPkl, classificationDatasetAsForceFile


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

    def test_formularEvalsTo_notFinite_forSomeInputs(self):
        filenameFeatures, filenameLabels = classificationDatasetAsForceFile
        alg = PrepareRegressionDatasetFromFilesAlgorithm()
        parameters = {
            alg.P_FEATURE_FILE: filenameFeatures,
            alg.P_VALUE_FILE: filenameLabels,
            alg.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        self.runalg(alg, parameters)

        alg = SpectralIndexOptimizerAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('dataset.pkl'),
            alg.P_OUTPUT_MATRIX: self.filename('scores.tif')
        }
        self.runalg(alg, parameters)
