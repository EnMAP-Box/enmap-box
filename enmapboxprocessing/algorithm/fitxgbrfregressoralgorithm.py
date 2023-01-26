from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitXGBRFRegressorAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit XGBRFRegressor'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://xgboost.readthedocs.io/en/stable/">XGBoost</a> random forest regression.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://xgboost.readthedocs.io/en/latest/python/python_api.html?highlight=XGBRFRegressor#xgboost.XGBRFRegressor' \
               '">XGBRFRegressor</a> for information on different parameters.'

    def code(cls):
        from xgboost import XGBRFRegressor

        regressor = XGBRFRegressor(n_estimators=100)
        return regressor
