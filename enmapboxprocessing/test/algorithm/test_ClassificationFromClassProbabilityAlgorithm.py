from enmapbox.exampledata import landcover_polygons
from enmapboxprocessing.algorithm.classificationfromclassprobabilityalgorithm import \
    ClassificationFromClassProbabilityAlgorithm
from enmapboxprocessing.algorithm.roccurvealgorithm import RocCurveAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import fraction_map_l3, fraction_polygons_l3, landcover_map_l3, landcover_polygons_3classes

openReport = True


class TestClassificationFromClassProbabilityAlgorithm(TestCase):

    def test(self):
        alg = ClassificationFromClassProbabilityAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_PROBABILITY: fraction_map_l3,
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif'),
        }
        self.runalg(alg, parameters)
