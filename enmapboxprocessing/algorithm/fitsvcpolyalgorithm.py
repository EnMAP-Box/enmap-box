from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from typeguard import typechecked


@typechecked
class FitSvcPolyAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit SVC (polynomial kernel)'

    def shortDescription(self) -> str:
        return 'C-Support Vector Classification. ' \
               '\nThe implementation is based on libsvm. The fit time scales at least quadratically with the number ' \
               'of samples and may be impractical beyond tens of thousands of samples. ' \
               '\nThe multiclass support is handled according to a one-vs-one scheme.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See ' \
               '<a href="' \
               'http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html' \
               '">SVC</a>, ' \
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
        from sklearn.svm import SVC

        svc = SVC(probability=False)
        param_grid = {'kernel': ['poly'],
                      'coef0': [0],
                      'degree': [3],
                      'gamma': [0.001, 0.01, 0.1, 1, 10, 100, 1000],
                      'C': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
        tunedSVC = GridSearchCV(cv=3, estimator=svc, scoring='f1_macro', param_grid=param_grid)
        classifier = make_pipeline(StandardScaler(), tunedSVC)
        return classifier
