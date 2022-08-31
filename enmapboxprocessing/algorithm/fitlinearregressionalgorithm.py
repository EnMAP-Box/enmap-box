from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from typeguard import typechecked


@typechecked
class FitLinearRegressionAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit LinearRegression'

    def shortDescription(self) -> str:
        return 'Ordinary least squares Linear Regression.\n' \
               'LinearRegression fits a linear model with coefficients w = (w1, ..., wp) to minimize the residual ' \
               'sum of squares between the observed targets in the dataset, and the targets predicted by the ' \
               'linear approximation.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html' \
               '">LinearRegression</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LinearRegression

        linearRegression = LinearRegression()
        regressor = make_pipeline(StandardScaler(), linearRegression)
        return regressor
