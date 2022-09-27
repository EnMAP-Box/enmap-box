from sklearn.base import TransformerMixin

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.fitfactoranalysisalgorithm import FitFactorAnalysisAlgorithm
from enmapboxprocessing.algorithm.fitfasticaalgorithm import FitFastIcaAlgorithm
from enmapboxprocessing.algorithm.fitfeatureagglomerationalgorithm import FitFeatureAgglomerationAlgorithm
from enmapboxprocessing.algorithm.fitkernelpcaalgorithm import FitKernelPcaAlgorithm
from enmapboxprocessing.algorithm.fitmaxabsscaleralgorithm import FitMaxAbsScalerAlgorithm
from enmapboxprocessing.algorithm.fitminmaxscaleralgorithm import FitMinMaxScalerAlgorithm
from enmapboxprocessing.algorithm.fitnormalizeralgorithm import FitNormalizerAlgorithm
from enmapboxprocessing.algorithm.fitpcaalgorithm import FitPcaAlgorithm
from enmapboxprocessing.algorithm.fitquantiletransformeralgorithm import FitQuantileTransformerAlgorithm
from enmapboxprocessing.algorithm.fitrobustscaleralgorithm import FitRobustScalerAlgorithm
from enmapboxprocessing.algorithm.fitstandardscaleralgorithm import FitStandardScalerAlgorithm
from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import classifierDumpPkl
from qgis.core import QgsProcessingException


class FitTestTransformerAlgorithm(FitTransformerAlgorithmBase):

    def displayName(self) -> str:
        return ''

    def shortDescription(self) -> str:
        return ''

    def helpParameterCode(self) -> str:
        return ''

    def code(self) -> TransformerMixin:
        from sklearn.decomposition import PCA
        transformer = PCA(n_components=3, random_state=42)
        return transformer


class TestFitClassifierAlgorithm(TestCase):

    def test_fit_withDataset(self):
        alg = FitTestTransformerAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_TRANSFORMER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_TRANSFORMER: self.filename('transformer.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_TRANSFORMER]))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertEqual((58, 177), dump.X.shape)
        self.assertIsInstance(dump.transformer, TransformerMixin)
        self.assertEqual(3, dump.transformer.n_components_)

    def test_fit_withRaster1(self):
        alg = FitTestTransformerAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_TRANSFORMER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_TRANSFORMER: self.filename('transformer.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_TRANSFORMER]))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertEqual((836, 177), dump.X.shape)
        self.assertIsInstance(dump.transformer, TransformerMixin)
        self.assertEqual(3, dump.transformer.n_components_)

    def test_fit_withRaster2(self):
        alg = FitTestTransformerAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_SAMPLE_SIZE: 0,
            alg.P_TRANSFORMER: alg.defaultCodeAsString(),
            alg.P_OUTPUT_TRANSFORMER: self.filename('transformer.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_TRANSFORMER]))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertEqual((71158, 177), dump.X.shape)
        self.assertIsInstance(dump.transformer, TransformerMixin)
        self.assertEqual(3, dump.transformer.n_components_)

    def test_error(self):
        alg = FitTestTransformerAlgorithm()
        parameters = {
            alg.P_DATASET: classifierDumpPkl,
            alg.P_FEATURE_RASTER: enmap,
            alg.P_OUTPUT_TRANSFORMER: self.filename('transformer.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual(
                'Mutually exclusive parameters, select either Raster layer with features, or Training dataset',
                str(error)
            )

    def test_transformers(self):
        algs = [
            FitPcaAlgorithm(),
            FitFastIcaAlgorithm(),
            FitFactorAnalysisAlgorithm(),
            FitFeatureAgglomerationAlgorithm(),
            FitKernelPcaAlgorithm(),
            FitMinMaxScalerAlgorithm(),
            FitNormalizerAlgorithm(),
            FitQuantileTransformerAlgorithm(),
            FitRobustScalerAlgorithm(),
            FitStandardScalerAlgorithm(),
            FitMaxAbsScalerAlgorithm()
        ]
        for alg in algs:
            print(alg.displayName())
            alg.initAlgorithm()
            alg.shortHelpString()
            parameters = {
                alg.P_DATASET: classifierDumpPkl,
                alg.P_TRANSFORMER: alg.defaultCodeAsString(),
                alg.P_OUTPUT_TRANSFORMER: self.filename('transformer.pkl')
            }
            self.runalg(alg, parameters)
