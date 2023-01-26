from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxexternal.typeguard import typechecked


@typechecked
class FitGenericClassifierAlgorithm(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return 'Fit generic classifier'

    def shortDescription(self) -> str:
        return 'A generic classifier.'

    def helpParameterCode(self) -> str:
        return 'Scikit-learn python code.'

    def code(cls):
        from sklearn.dummy import DummyClassifier

        classifier = DummyClassifier()
        return classifier
