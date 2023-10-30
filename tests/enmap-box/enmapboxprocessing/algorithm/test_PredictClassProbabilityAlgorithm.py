import numpy as np
from sklearn.base import ClassifierMixin

from tests.enmapboxtestdata import enmap
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.predictclassprobabilityalgorithm import PredictClassPropabilityAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from tests.enmapboxtestdata import classifierDumpPkl

writeToDisk = True


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


class TestPredictClassProbabilityAlgorithm(TestCase):

    def test_default(self):
        algFit = FitTestClassifierAlgorithm()
        algFit.initAlgorithm()
        parametersFit = {
            algFit.P_DATASET: classifierDumpPkl,
            algFit.P_CLASSIFIER: algFit.defaultCodeAsString(),
            algFit.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl'),
        }
        self.runalg(algFit, parametersFit)

        alg = PredictClassPropabilityAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_CLASSIFIER: parametersFit[algFit.P_OUTPUT_CLASSIFIER],
            alg.P_OUTPUT_PROBABILITY: self.filename('probability1.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(-13052, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_PROBABILITY]).array())))
