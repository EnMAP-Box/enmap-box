from sklearn.base import RegressorMixin

from enmapboxprocessing.algorithm.fitgaussianprocessregressoralgorithm import FitGaussianProcessRegressorAlgorithm
from enmapboxprocessing.algorithm.fitkernelridgealgorithm import FitKernelRidgeAlgorithm
from enmapboxprocessing.algorithm.fitlinearregressionalgorithm import FitLinearRegressionAlgorithm
from enmapboxprocessing.algorithm.fitlinearsvralgorithm import FitLinearSVRAlgorithm
from enmapboxprocessing.algorithm.fitplsegressionalgorithm import FitPLSRegressionAlgorithm
from enmapboxprocessing.algorithm.fitrandomforestregressoralgorithm import FitRandomForestRegressorAlgorithm
from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import regressorDumpPkl, regressorDumpSingleTargetPkl


class FitTestRegressorAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return ''

    def shortDescription(self) -> str:
        return ''

    def helpParameterCode(self) -> str:
        return ''

    def code(self) -> RegressorMixin:
        from sklearn.ensemble import RandomForestRegressor
        regressor = RandomForestRegressor(n_estimators=10, oob_score=True, random_state=42)
        return regressor


class TestFitRegressorAlgorithm(TestCase):

    def test_fitMultiTarget(self):
        alg = FitTestRegressorAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpPkl,
            alg.P_REGRESSOR: alg.defaultCodeAsString(),
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl')
        }
        self.runalg(alg, parameters)

    def test_fitSingleTarget(self):
        alg = FitTestRegressorAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_REGRESSOR: alg.defaultCodeAsString(),
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl')
        }
        self.runalg(alg, parameters)

    def test_unfitted(self):
        alg = FitTestRegressorAlgorithm()
        parameters = {
            alg.P_DATASET: None,
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl')
        }
        self.runalg(alg, parameters)

    def test_regressors(self):
        algs = [
            FitRandomForestRegressorAlgorithm(),
            FitGaussianProcessRegressorAlgorithm(),
            FitLinearRegressionAlgorithm(),
            FitKernelRidgeAlgorithm(),
            FitLinearSVRAlgorithm(),
            FitPLSRegressionAlgorithm(),
        ]
        for alg in algs:
            print(alg.displayName())
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_DATASET: regressorDumpPkl,
                alg.P_REGRESSOR: alg.defaultCodeAsString(),
                alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl')
            }
            self.runalg(alg, parameters)
