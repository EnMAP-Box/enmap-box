from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitLGBMClassifierAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit LGBMClassifier'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://lightgbm.readthedocs.io/">LightGBM</a> classifier.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html#lightgbm-lgbmclassifier' \
               '">LGBMClassifier</a> for information on different parameters.'

    def code(cls):
        from lightgbm import LGBMClassifier
        classifier = LGBMClassifier(n_estimators=100)
        return classifier
