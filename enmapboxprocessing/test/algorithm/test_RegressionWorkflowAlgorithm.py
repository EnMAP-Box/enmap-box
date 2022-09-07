from sklearn.base import RegressorMixin

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.regressionworkflowalgorithm import RegressionWorkflowAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import regressor_pkl

openReport = True


class FitTestRegressorAlgorithm(FitClassifierAlgorithmBase):

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


class TestRegressionWorkflowAlgorithm(TestCase):

    def test(self):
        alg = RegressionWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: regressor_pkl,
            alg.P_REGRESSOR: FitTestRegressorAlgorithm().defaultCodeAsString(),
            alg.P_RASTER: enmap,
            alg.P_NFOLD: 10,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
            alg.P_OUTPUT_REGRESSION: self.filename('regression.tif'),
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)
