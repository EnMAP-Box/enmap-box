from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.fitrandomforestregressoralgorithm import FitRandomForestRegressorAlgorithm
from enmapboxprocessing.algorithm.regressionbasedunmixingalgorithm import RegressionBasedUnmixingAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import classifier_pkl


class TestFitClassifierAlgorithm(TestCase):

    def test(self):
        alg = RegressionBasedUnmixingAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
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
