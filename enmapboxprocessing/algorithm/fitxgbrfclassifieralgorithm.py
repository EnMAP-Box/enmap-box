from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from typeguard import typechecked


@typechecked
class FitXGBRFClassifierAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit XGBRFClassifier'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://xgboost.readthedocs.io/en/stable/">XGBoost</a> random forest classification.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://xgboost.readthedocs.io/en/latest/python/python_api.html?highlight=XGBRFClassifier#xgboost.XGBRFClassifier' \
               '">XGBRFClassifier</a> for information on different parameters.'

    def code(cls):
        from xgboost import XGBRFClassifier
        classifier = XGBRFClassifier(n_estimators=100)
        return classifier
