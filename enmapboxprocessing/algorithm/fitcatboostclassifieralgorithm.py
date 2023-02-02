from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapbox.typeguard import typechecked


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
