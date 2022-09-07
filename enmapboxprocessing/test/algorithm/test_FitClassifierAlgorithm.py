from sklearn.base import ClassifierMixin

from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.fitgaussianprocessclassifieralgorithm import FitGaussianProcessClassifierAlgorithm
from enmapboxprocessing.algorithm.fitgenericclassifieralgorithm import FitGenericClassifierAlgorithm
from enmapboxprocessing.algorithm.fitlinearsvcalgorithm import FitLinearSvcAlgorithm
from enmapboxprocessing.algorithm.fitrandomforestclassifieralgorithm import FitRandomForestClassifierAlgorithm
from enmapboxprocessing.algorithm.fitsvcpolyalgorithm import FitSvcPolyAlgorithm
from enmapboxprocessing.algorithm.fitsvcrbfalgorithm import FitSvcRbfAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import (classifier_pkl)


class FitTestClassifierAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return ''

    def shortDescription(self) -> str:
        return ''

    def helpParameterCode(self) -> str:
        return ''

    def code(self) -> ClassifierMixin:
        from sklearn.ensemble import RandomForestClassifier
        classifier = RandomForestClassifier(n_estimators=10, oob_score=True, random_state=42)
        return classifier


class TestFitClassifierAlgorithm(TestCase):

    def test_fitted(self):
        alg = FitTestClassifierAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_CLASSIFIER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        self.runalg(alg, parameters)

    def test_fit_and_predict(self):
        alg = FitTestClassifierAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_CLASSIFIER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        self.runalg(alg, parameters)

    def test_unfitted(self):
        alg = FitTestClassifierAlgorithm()
        parameters = {
            alg.P_DATASET: None,
            alg.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        self.runalg(alg, parameters)

    def test_code(self):
        alg = FitGenericClassifierAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: 'from sklearn.linear_model import LogisticRegression\n'
                              'classifier = LogisticRegression(max_iter=1000)',
            alg.P_DATASET: classifier_pkl,
            alg.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        self.runalg(alg, parameters)

    def test_classifiers(self):
        algs = [
            FitRandomForestClassifierAlgorithm(), FitGaussianProcessClassifierAlgorithm(), FitLinearSvcAlgorithm(),
            FitSvcRbfAlgorithm(), FitSvcPolyAlgorithm(),
        ]
        for alg in algs:
            print(alg.displayName())
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_DATASET: classifier_pkl,
                alg.P_CLASSIFIER: alg.defaultCodeAsString(),
                alg.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
            }
            self.runalg(alg, parameters)
