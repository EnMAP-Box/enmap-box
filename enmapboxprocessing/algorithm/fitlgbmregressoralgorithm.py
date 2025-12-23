from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitLGBMRegressorAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit LGBMRegressor'

    def shortDescription(self) -> str:
        return 'Implementation of the scikit-learn API for ' \
               '<a href="https://lightgbm.readthedocs.io/">LightGBM </a> regressor.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMRegressor.html#lightgbm-lgbmregressor' \
               '">LGBMRegressor</a> for information on different parameters.'

    def code(cls):
        from lightgbm import LGBMRegressor

        regressor = LGBMRegressor(n_estimators=100)
        return regressor
