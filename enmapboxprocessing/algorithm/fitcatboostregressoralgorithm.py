from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitCatBoostRegressorAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit CatBoostRegressor'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://catboost.ai/en/docs/">CatBoost</a> regressor.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://catboost.ai/en/docs/concepts/python-reference_catboostregressor' \
               '">CatBoostRegressor</a> for information on different parameters.'

    def code(cls):
        from catboost import CatBoostRegressor
        regressor = CatBoostRegressor(n_estimators=100)
        return regressor
