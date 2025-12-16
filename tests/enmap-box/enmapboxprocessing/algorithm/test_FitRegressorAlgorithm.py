import unittest

import sklearn
from sklearn.base import RegressorMixin

from enmapboxprocessing.algorithm.fitcatboostregressoralgorithm import FitCatBoostRegressorAlgorithm
from enmapboxprocessing.algorithm.fitgaussianprocessregressoralgorithm import FitGaussianProcessRegressorAlgorithm
from enmapboxprocessing.algorithm.fitkernelridgealgorithm import FitKernelRidgeAlgorithm
from enmapboxprocessing.algorithm.fitlinearregressionalgorithm import FitLinearRegressionAlgorithm
from enmapboxprocessing.algorithm.fitlinearsvralgorithm import FitLinearSvrAlgorithm
from enmapboxprocessing.algorithm.fitplsegressionalgorithm import FitPLSRegressionAlgorithm
from enmapboxprocessing.algorithm.fitrandomforestregressoralgorithm import FitRandomForestRegressorAlgorithm
from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import regressorDumpSingleTargetPkl, regressorDumpPkl, regressorDumpMultiTargetPkl

SKLEARN_VERSION = list(map(int, sklearn.__version__.split('.')))
SKLEARN_VERSION_NUMBER = SKLEARN_VERSION[0] + SKLEARN_VERSION[1] / 10


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
            FitLinearSvrAlgorithm(),
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

    def test_debug_issue967(self):
        alg = FitLinearSvrAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpMultiTargetPkl,
            alg.P_REGRESSOR: alg.defaultCodeAsString(),
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor1.pkl')
        }
        self.runalg(alg, parameters)

        alg = FitLinearSvrAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_REGRESSOR: alg.defaultCodeAsString(),
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor2.pkl')
        }
        self.runalg(alg, parameters)

    @unittest.skipIf(SKLEARN_VERSION_NUMBER >= 1.8, 'CatBoost not compatible with sklearn >= 1.8')
    def test_issue790(self):
        alg = FitCatBoostRegressorAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_REGRESSOR: alg.defaultCodeAsString(),
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl')
        }
        self.runalg(alg, parameters)
