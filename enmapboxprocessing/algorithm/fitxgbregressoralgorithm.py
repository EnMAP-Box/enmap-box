from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from typeguard import typechecked


@typechecked
class FitXGBRegressorAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit XGBRegressor'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://xgboost.readthedocs.io/en/stable/">XGBoost</a> regression.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://xgboost.readthedocs.io/en/latest/python/python_api.html?highlight=XGBRegressor#xgboost.XGBRegressor' \
               '">XGBRegressor</a> for information on different parameters.'

    def code(cls):
        from xgboost import XGBRegressor

        regressor = XGBRegressor(n_estimators=100)
        return regressor
