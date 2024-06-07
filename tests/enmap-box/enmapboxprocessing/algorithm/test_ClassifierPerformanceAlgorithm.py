from enmapboxprocessing.algorithm.classifierperformancealgorithm import ClassifierPerformanceAlgorithm
from enmapboxprocessing.algorithm.fitsvcrbfalgorithm import FitSvcRbfAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import classifierDumpPkl


class TestClassifierPerformanceAlgorithm(TestCase):

    def test_trainPerformance(self):
        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifierDumpPkl,
            alg.P_DATASET: classifierDumpPkl,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_train.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_crossPerformance(self):
        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifierDumpPkl,
            alg.P_DATASET: classifierDumpPkl,
            alg.P_NFOLD: 3,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_crossval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_oobPerformance(self):
        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifierDumpPkl,
            alg.P_DATASET: classifierDumpPkl,
            alg.P_NFOLD: 1,
            alg.P_OPEN_REPORT: not self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_oobval.html')
        }
        self.runalg(alg, parameters)
        # check the result manually

    def test_oobNotSupported(self):

        alg0 = FitSvcRbfAlgorithm()
        parameters0 = {
            alg0.P_CLASSIFIER: alg0.defaultCodeAsString(),
            alg0.P_DATASET: classifierDumpPkl,
            alg0.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        self.runalg(alg0, parameters0)

        alg = ClassifierPerformanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: parameters0[alg0.P_OUTPUT_CLASSIFIER],
            alg.P_DATASET: classifierDumpPkl,
            alg.P_NFOLD: 1,
            alg.P_OPEN_REPORT: not self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report_oobval.html')
        }
        try:
            self.runalg(alg, parameters)
        except Exception as error:
            self.assertTrue(str(error).startswith('classifier not supporting out-of-bag estimates'))
