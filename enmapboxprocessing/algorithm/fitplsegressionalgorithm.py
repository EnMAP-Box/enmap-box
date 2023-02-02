from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitPLSRegressionAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit PLSRegression'

    def shortDescription(self) -> str:
        return 'Partial Least Squares regression.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.cross_decomposition.PLSRegression.html' \
               '">PLSRegression</a> for information on different parameters.'

    def code(cls):
        from sklearn.cross_decomposition import PLSRegression

        regressor = PLSRegression(n_components=2)
        return regressor
