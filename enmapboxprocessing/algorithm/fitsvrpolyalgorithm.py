from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from typeguard import typechecked


@typechecked
class FitSvrPolyAlgorithm(FitRegressorAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit SVR (polynomial kernel)'

    def shortDescription(self) -> str:
        return 'Epsilon-Support Vector Regression.\n' \
               'The free parameters in the model are C and epsilon.\n' \
               'The implementation is based on libsvm. The fit time complexity is more than quadratic with the ' \
               'number of samples which makes it hard to scale to datasets with more than a couple of 10000 samples.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See ' \
               '<a href="' \
               'http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html' \
               '">SVR</a>, ' \
               '<a href="' \
               'http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html' \
               '">GridSearchCV</a>, ' \
               '<a href="' \
               'http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html' \
               '">StandardScaler</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.model_selection import GridSearchCV
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVR

        svr = SVR()
        param_grid = {'kernel': ['poly'],
                      'epsilon': [0.],
                      'coef0': [0],
                      'degree': [3],
                      'gamma': [0.001, 0.01, 0.1, 1, 10, 100, 1000],
                      'C': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
        tunedSVR = GridSearchCV(cv=3, estimator=svr, scoring='neg_mean_absolute_error', param_grid=param_grid)
        regressor = make_pipeline(StandardScaler(), tunedSVR)
        return regressor
