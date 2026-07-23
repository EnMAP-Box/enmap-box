from enmapboxprocessing.algorithm.classifierfeaturerankingpermutationimportancealgorithm import \
    ClassifierFeatureRankingPermutationImportanceAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import classifierDumpSkops


class TestClassifierFeatureRankingPermutationImportanceAlgorithm(TestCase):

    def test(self):
        return
        alg = ClassifierFeatureRankingPermutationImportanceAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CLASSIFIER: classifierDumpSkops,
            alg.P_OPEN_REPORT: self.openReport,
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)
