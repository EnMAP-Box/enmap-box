from io import StringIO

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase


@typechecked
class FitCatBoostClassifierAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit CatBoostClassifier'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://catboost.ai/en/docs/">CatBoost</a> classifier.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://catboost.ai/en/docs/concepts/python-reference_catboostclassifier' \
               '">CatBoostClassifier</a> for information on different parameters.'

    def code(cls):
        from catboost import CatBoostClassifier
        classifier = CatBoostClassifier(n_estimators=100)
        return classifier


# monkey patch for issue #790
try:
    import catboost.core

    stringIO = StringIO()

    def _get_stream_like_object_FIXED(obj):
        return stringIO

    catboost.core._get_stream_like_object = _get_stream_like_object_FIXED
except Exception:
    pass
