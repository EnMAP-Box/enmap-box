from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitGaussianProcessRegressorAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit GaussianProcessRegressor'

    def shortDescription(self) -> str:
        return 'Gaussian process regression (GPR).'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcessRegressor.html' \
               '">GaussianProcessRegressor</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF

        gpr = GaussianProcessRegressor(RBF())
        regressor = make_pipeline(StandardScaler(), gpr)
        return regressor
