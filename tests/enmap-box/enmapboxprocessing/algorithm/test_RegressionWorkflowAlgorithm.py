import unittest

from osgeo import gdal
from sklearn.base import RegressorMixin

from enmapboxprocessing.algorithm.fitcatboostregressoralgorithm import FitCatBoostRegressorAlgorithm
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.fitlinearsvralgorithm import FitLinearSvrAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectoralgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAlgorithm
from enmapboxprocessing.algorithm.regressionworkflowalgorithm import RegressionWorkflowAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap, enmap_potsdam, veg_cover_fraction_potsdam_point, regressorDumpSingleTargetPkl
from enmapboxtestdata import regressorDumpMultiTargetPkl


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


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestRegressionWorkflowAlgorithm(TestCase):

    def test(self):
        alg = RegressionWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpMultiTargetPkl,
            alg.P_REGRESSOR: FitTestRegressorAlgorithm().defaultCodeAsString(),
            alg.P_RASTER: enmap,
            alg.P_NFOLD: 10,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
            alg.P_OUTPUT_REGRESSION: self.filename('regression.tif'),
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)

    def test_catBoost_singleTarget(self):

        try:
            import catboost
        except ModuleNotFoundError:
            return

        print(catboost.version)

        alg = RegressionWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpSingleTargetPkl,
            alg.P_REGRESSOR: FitCatBoostRegressorAlgorithm().defaultCodeAsString(),
            alg.P_RASTER: enmap,
            alg.P_NFOLD: 3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
            alg.P_OUTPUT_REGRESSION: self.filename('regression.tif'),
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)

    def test_catBoost_multiTarget(self):
        try:
            import catboost
        except ModuleNotFoundError:
            return

        print(catboost.version)

        alg = RegressionWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpMultiTargetPkl,
            alg.P_REGRESSOR: FitCatBoostRegressorAlgorithm().defaultCodeAsString(),
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
            alg.P_OUTPUT_REGRESSION: self.filename('regression.tif'),
        }
        self.runalg(alg, parameters)

    def test_linearSvrAlgorithm(self):
        alg = RegressionWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpMultiTargetPkl,
            alg.P_REGRESSOR: FitLinearSvrAlgorithm().defaultCodeAsString(),
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
            alg.P_OUTPUT_REGRESSION: self.filename('regression.tif'),
        }
        self.runalg(alg, parameters)

    def _DISABLED_test_trainingOnly(self):
        alg = RegressionWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: regressorDumpMultiTargetPkl,
            alg.P_REGRESSOR: FitTestRegressorAlgorithm().defaultCodeAsString(),
            alg.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
        }
        self.runalg(alg, parameters)

    def test_badBandsHandling_withNameMatching(self):
        alg1 = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters1 = {
            alg1.P_CONTINUOUS_VECTOR: veg_cover_fraction_potsdam_point,
            alg1.P_FEATURE_RASTER: enmap_potsdam,
            alg1.P_EXCLUDE_BAD_BANDS: True,
            alg1.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        self.runalg(alg1, parameters1)

        alg2 = RegressionWorkflowAlgorithm()
        parameters2 = {
            alg2.P_DATASET: parameters1[alg1.P_OUTPUT_DATASET],
            alg2.P_REGRESSOR: FitTestRegressorAlgorithm().defaultCodeAsString(),
            alg2.P_RASTER: enmap_potsdam,
            alg2.P_MATCH_BY_NAME: True,
            alg2.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
            alg2.P_OUTPUT_REGRESSION: self.filename('regression.tif')
        }
        self.runalg(alg2, parameters2)

    def test_badBandsHandling_withoutNameMatching(self):
        alg1 = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters1 = {
            alg1.P_CONTINUOUS_VECTOR: veg_cover_fraction_potsdam_point,
            alg1.P_FEATURE_RASTER: enmap_potsdam,
            alg1.P_EXCLUDE_BAD_BANDS: True,
            alg1.P_OUTPUT_DATASET: self.filename('dataset.pkl')
        }
        self.runalg(alg1, parameters1)

        alg2 = RegressionWorkflowAlgorithm()
        parameters2 = {
            alg2.P_DATASET: parameters1[alg1.P_OUTPUT_DATASET],
            alg2.P_REGRESSOR: FitTestRegressorAlgorithm().defaultCodeAsString(),
            alg2.P_RASTER: enmap_potsdam,
            alg2.P_MATCH_BY_NAME: False,
            alg2.P_OUTPUT_REGRESSOR: self.filename('regressor.pkl'),
            alg2.P_OUTPUT_REGRESSION: self.filename('regression.tif')
        }
        self.runalg(alg2, parameters2)
