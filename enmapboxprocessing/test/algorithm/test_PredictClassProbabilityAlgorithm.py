import numpy as np
from sklearn.base import ClassifierMixin

from enmapbox.exampledata import enmap, landcover_polygons
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.predictclassprobabilityalgorithm import PredictClassPropabilityAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import landcover_raster_30m_tif, classifier_pkl

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
            algFit.P_DATASET: classifier_pkl,
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

    def test_rasterMask(self):
        algFit = FitTestClassifierAlgorithm()
        algFit.initAlgorithm()
        parametersFit = {
            algFit.P_DATASET: classifier_pkl,
            algFit.P_CLASSIFIER: algFit.defaultCodeAsString(),
            algFit.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        self.runalg(algFit, parametersFit)

        alg = PredictClassPropabilityAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_CLASSIFIER: parametersFit[algFit.P_OUTPUT_CLASSIFIER],
            alg.P_MASK: landcover_raster_30m_tif,
            alg.P_OUTPUT_PROBABILITY: self.filename('probability2.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(-427832, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_PROBABILITY]).array())))

    def test_vectorMask(self):
        algFit = FitTestClassifierAlgorithm()
        algFit.initAlgorithm()
        parametersFit = {
            algFit.P_DATASET: classifier_pkl,
            algFit.P_CLASSIFIER: algFit.defaultCodeAsString(),
            algFit.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        self.runalg(algFit, parametersFit)

        alg = PredictClassPropabilityAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_CLASSIFIER: parametersFit[algFit.P_OUTPUT_CLASSIFIER],
            alg.P_MASK: landcover_polygons,
            alg.P_OUTPUT_PROBABILITY: self.filename('probability3.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(-427832, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_PROBABILITY]).array())))
