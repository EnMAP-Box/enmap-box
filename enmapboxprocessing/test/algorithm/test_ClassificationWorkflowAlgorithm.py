from sklearn.base import ClassifierMixin

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.classificationworkflowalgorithm import ClassificationWorkflowAlgorithm
from enmapboxprocessing.algorithm.fitcatboostclassifieralgorithm import FitCatBoostClassifierAlgorithm
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import classifierDumpPkl

openReport = True


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


class TestClassificationAlgorithm(TestCase):

    def test(self):
        alg = ClassificationWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_CLASSIFIER: FitTestClassifierAlgorithm().defaultCodeAsString(),
            alg.P_RASTER: enmap,
            alg.P_NFOLD: 10,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl'),
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif'),
            alg.P_OUTPUT_PROBABILITY: self.filename('probability.tif'),
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)

    def _test_debug_issue1140(self):
        alg = ClassificationWorkflowAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_CLASSIFIER: FitCatBoostClassifierAlgorithm().defaultCodeAsString(),
            alg.P_RASTER: enmap,
            alg.P_OPEN_REPORT: openReport,
            alg.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl'),
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif'),
            alg.P_OUTPUT_PROBABILITY: self.filename('probability.tif'),
        }
        self.runalg(alg, parameters)
