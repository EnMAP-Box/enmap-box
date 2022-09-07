from enmapboxprocessing.algorithm.classificationfromclassprobabilityalgorithm import \
    ClassificationFromClassProbabilityAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import fraction_map_l3_tif

openReport = True


class TestClassificationFromClassProbabilityAlgorithm(TestCase):

    def test(self):
        alg = ClassificationFromClassProbabilityAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_PROBABILITY: fraction_map_l3_tif,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif'),
        }
        self.runalg(alg, parameters)
