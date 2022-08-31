from enmapboxprocessing.algorithm.featureclusteringhierarchicalalgorithm import FeatureClusteringHierarchicalAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import classifierDumpPkl


class TestFeatureClusteringHierarchicalAlgorithm(TestCase):

    def test(self):
        alg = FeatureClusteringHierarchicalAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_OPEN_REPORT: False,
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)
