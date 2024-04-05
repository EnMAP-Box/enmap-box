from io import StringIO

from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapbox.typeguard import typechecked


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


# monkey patch for issue #790
try:
    import catboost.core
    stringIO = StringIO()

    def _get_stream_like_object_FIXED(obj):
        return stringIO

    catboost.core._get_stream_like_object = _get_stream_like_object_FIXED
except Exception:
    pass
