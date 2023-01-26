from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitXGBClassifierAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit XGBClassifier'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://xgboost.readthedocs.io/en/stable/">XGBoost</a> classification.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://xgboost.readthedocs.io/en/latest/python/python_api.html?highlight=XGBClassifier#xgboost.XGBClassifier' \
               '">XGBClassifier</a> for information on different parameters.'

    def code(cls):
        from xgboost import XGBClassifier
        classifier = XGBClassifier(n_estimators=100)
        return classifier
