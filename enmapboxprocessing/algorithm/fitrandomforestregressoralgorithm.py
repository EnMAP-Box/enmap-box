from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitRandomForestRegressorAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit RandomForestRegressor'

    def shortDescription(self) -> str:
        return 'A random forest regressor.\n' \
               'A random forest is a meta estimator that fits a number of classifying decision trees on various ' \
               'sub-samples of the dataset and uses averaging to improve the predictive accuracy and control ' \
               'over-fitting. The sub-sample size is controlled with the max_samples parameter if bootstrap=True ' \
               '(default), otherwise the whole dataset is used to build each tree.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html' \
               '">RandomForestRegressor</a> for information on different parameters.'

    def code(cls):
        from sklearn.ensemble import RandomForestRegressor
        regressor = RandomForestRegressor(n_estimators=100, oob_score=True)
        return regressor
