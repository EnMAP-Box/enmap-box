import numpy as np
from sklearn.base import ClassifierMixin

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.creatergbimagefromclassprobabilityalgorithm import \
    CreateRgbImageFromClassProbabilityAlgorithm
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.predictclassificationalgorithm import PredictClassificationAlgorithm
from enmapboxprocessing.algorithm.predictclassprobabilityalgorithm import PredictClassPropabilityAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingException
from testdata import classifier_pkl


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


class TestCreateRgbImageFromClassProbabilityAlgorithm(TestCase):

    def test_colorsFromLayer(self):
        global c
        algFit = FitTestClassifierAlgorithm()
        algFit.initAlgorithm()
        parametersFit = {
            algFit.P_DATASET: classifier_pkl,
            algFit.P_CLASSIFIER: algFit.defaultCodeAsString(),
            algFit.P_OUTPUT_CLASSIFIER: self.filename('classifier.pkl')
        }
        result = self.runalg(algFit, parametersFit)

        algPredict1 = PredictClassificationAlgorithm()
        algPredict1.initAlgorithm()
        parametersPredict1 = {
            algPredict1.P_RASTER: enmap,
            algPredict1.P_CLASSIFIER: parametersFit[algFit.P_OUTPUT_CLASSIFIER],
            algPredict1.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif')
        }
        result = self.runalg(algPredict1, parametersPredict1)

        algPredict2 = PredictClassPropabilityAlgorithm()
        algPredict2.initAlgorithm()
        parametersPredict2 = {
            algPredict2.P_RASTER: enmap,
            algPredict2.P_CLASSIFIER: parametersFit[algFit.P_OUTPUT_CLASSIFIER],
            algPredict2.P_OUTPUT_PROBABILITY: self.filename('probability.tif')
        }
        result = self.runalg(algPredict2, parametersPredict2)

        # test colors from layer
        alg = CreateRgbImageFromClassProbabilityAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_PROBABILITY: parametersPredict2[algPredict2.P_OUTPUT_PROBABILITY],
            alg.P_COLORS_LAYER: parametersPredict1[algPredict1.P_OUTPUT_CLASSIFICATION],
            alg.P_OUTPUT_RGB: self.filename('rgb.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(16826968, np.sum(RasterReader(result[alg.P_OUTPUT_RGB]).array()))

        # test colors from list
        colors = str([c.color for c in ClassifierDump(**Utils.pickleLoad(classifier_pkl)).categories])
        parameters = {
            alg.P_PROBABILITY: parametersPredict2[algPredict2.P_OUTPUT_PROBABILITY],
            alg.P_COLORS: colors,
            alg.P_OUTPUT_RGB: self.filename('rgb.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(16826968, np.sum(RasterReader(result[alg.P_OUTPUT_RGB]).array()))

        # test invalid colors
        parameters = {
            alg.P_PROBABILITY: parametersPredict2[algPredict2.P_OUTPUT_PROBABILITY],
            alg.P_OUTPUT_RGB: self.filename('rgb.tif')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Category colors not specified.', str(error))

        colors = ''
        parameters = {
            alg.P_PROBABILITY: parametersPredict2[algPredict2.P_OUTPUT_PROBABILITY],
            alg.P_COLORS: colors,
            alg.P_OUTPUT_RGB: self.filename('rgb.tif')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Category colors not specified.', str(error))

        colors = 'dummy'
        parameters = {
            alg.P_PROBABILITY: parametersPredict2[algPredict2.P_OUTPUT_PROBABILITY],
            alg.P_COLORS: colors,
            alg.P_OUTPUT_RGB: self.filename('rgb.tif')
        }

        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Invalid value list: Colors', str(error))

        colors = "'#FF0000'"
        parameters = {
            alg.P_PROBABILITY: parametersPredict2[algPredict2.P_OUTPUT_PROBABILITY],
            alg.P_COLORS: colors,
            alg.P_OUTPUT_RGB: self.filename('rgb.tif')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual('Number of bands (5) not matching number of category colors (1)', str(error))
