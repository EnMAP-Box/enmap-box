from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapbox.typeguard import typechecked


@typechecked
class FitLinearSvcAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit LinearSVC'

    def shortDescription(self) -> str:
        return 'Linear Support Vector Classification. ' \
               "\nSimilar to SVC with parameter kernel='linear', but implemented in terms of liblinear rather than " \
               'libsvm, so it has more flexibility in the choice of penalties and loss functions and should scale ' \
               'better to large numbers of samples. ' \
               '\nThis class supports both dense and sparse input and the multiclass support is handled according to ' \
               'a one-vs-the-rest scheme.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code. ' \
               'See ' \
               '<a href="http://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html">LinearSVC</a>, ' \
               '<a href="http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html">GridSearchCV</a>, ' \
               '<a href="' \
               'http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html' \
               '">StandardScaler</a> for information on different parameters.'

    def code(cls):
        from sklearn.pipeline import make_pipeline
        from sklearn.model_selection import GridSearchCV
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import LinearSVC

        svc = LinearSVC(dual=True)
        param_grid = {'C': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
        tunedSVC = GridSearchCV(cv=3, estimator=svc, scoring='f1_macro', param_grid=param_grid)
        classifier = make_pipeline(StandardScaler(), tunedSVC)
        return classifier
