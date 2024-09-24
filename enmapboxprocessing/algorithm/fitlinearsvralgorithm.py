from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitLinearSvrAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit LinearSVR'

    def shortDescription(self) -> str:
        return 'Linear Support Vector Regression.\n' \
               'Similar to SVR with parameter kernel=’linear’, but implemented in terms of liblinear rather than ' \
               'libsvm, so it has more flexibility in the choice of penalties and loss functions and should scale ' \
               'better to large numbers of samples.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See <a href="' \
               'https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVR.html' \
               '">LinearSVR</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.model_selection import GridSearchCV
        from sklearn.multioutput import MultiOutputRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import LinearSVR

        svr = LinearSVR(dual=True)
        param_grid = {'epsilon': [0.], 'C': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
        tunedSVR = GridSearchCV(cv=3, estimator=svr, scoring='neg_mean_absolute_error', param_grid=param_grid)
        scaledAndTunedSVR = make_pipeline(StandardScaler(), tunedSVR)
        regressor = MultiOutputRegressor(scaledAndTunedSVR)
        return regressor
