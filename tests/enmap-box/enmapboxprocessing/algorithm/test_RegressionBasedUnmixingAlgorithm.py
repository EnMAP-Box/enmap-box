import numpy as np

from enmapboxtestdata import enmap
from enmapboxprocessing.algorithm.fitrandomforestregressoralgorithm import FitRandomForestRegressorAlgorithm
from enmapboxprocessing.algorithm.regressionbasedunmixingalgorithm import RegressionBasedUnmixingAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import classificationDatasetAsPklFile

from enmapbox.testing import start_app

start_app()


class TestRegressionBasedUnmixingAlgorithm(TestCase):

    def test(self):
        alg = RegressionBasedUnmixingAlgorithm()
        parameters = {
            alg.P_DATASET: classificationDatasetAsPklFile,
            alg.P_RASTER: enmap,
            alg.P_REGRESSOR: FitRandomForestRegressorAlgorithm().defaultCodeAsString(),
            alg.P_N: 10,
            alg.P_BACKGROUND: 0,
            alg.P_INCLUDE_ENDMEMBER: False,
            alg.P_ENSEMBLE_SIZE: 3,
            alg.P_OUTPUT_FRACTION: self.filename('fraction.tif'),
            alg.P_OUTPUT_VARIATION: self.filename('variation.tif'),
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif')
        }
        self.runalg(alg, parameters)

    def test_sumToOne(self):
        alg = RegressionBasedUnmixingAlgorithm()
        parameters = {
            alg.P_DATASET: classificationDatasetAsPklFile,
            alg.P_RASTER: enmap,
            alg.P_REGRESSOR: FitRandomForestRegressorAlgorithm().defaultCodeAsString(),
            alg.P_N: 100,
            alg.P_BACKGROUND: 0,
            alg.P_INCLUDE_ENDMEMBER: False,
            alg.P_ENSEMBLE_SIZE: 3,
            alg.P_SUM_TO_ONE: True,
            alg.P_OUTPUT_FRACTION: self.filename('fraction.tif'),
            alg.P_OUTPUT_VARIATION: self.filename('variation.tif'),
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif')
        }
        self.runalg(alg, parameters)
        array = RasterReader(parameters[alg.P_OUTPUT_FRACTION]).array()
        self.assertListEqual([-5, 1], list(np.unique(np.round(np.sum(array, axis=0), 1))))
