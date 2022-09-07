from enmapboxprocessing.algorithm.featureclusteringhierarchicalalgorithm import FeatureClusteringHierarchicalAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import classifier_pkl


class TestFeatureClusteringHierarchicalAlgorithm(TestCase):

    def test(self):
        alg = FeatureClusteringHierarchicalAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_DATASET: classifier_pkl,
            alg.P_OPEN_REPORT: False,
            alg.P_OUTPUT_REPORT: self.filename('report.html')
        }
        self.runalg(alg, parameters)
