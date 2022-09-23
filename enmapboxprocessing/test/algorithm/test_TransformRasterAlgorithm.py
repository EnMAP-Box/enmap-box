import numpy as np
from sklearn.base import TransformerMixin

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.fittransformeralgorithmbase import FitTransformerAlgorithmBase
from enmapboxprocessing.algorithm.inversetransformrasteralgorithm import InverseTransformRasterAlgorithm
from enmapboxprocessing.algorithm.transformrasteralgorithm import TransformRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxtestdata import classifierDumpPkl


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


class TestTransformRasterAlgorithm(TestCase):

    def test(self):
        algFit = FitTestTransformerAlgorithm()
        algFit.initAlgorithm()
        parametersFit = {
            algFit.P_DATASET: classifierDumpPkl,
            algFit.P_TRANSFORMER: algFit.defaultCodeAsString(),
            algFit.P_OUTPUT_TRANSFORMER: self.filename('transformer.pkl'),
        }
        self.runalg(algFit, parametersFit)

        # forward transform
        alg1 = TransformRasterAlgorithm()
        alg1.initAlgorithm()
        parameters = {
            alg1.P_RASTER: enmap,
            alg1.P_TRANSFORMER: parametersFit[algFit.P_OUTPUT_TRANSFORMER],
            alg1.P_OUTPUT_RASTER: self.filename('transformation.tif')
        }
        result = self.runalg(alg1, parameters)
        self.assertAlmostEqual(35872.2, np.max(RasterReader(result[alg1.P_OUTPUT_RASTER]).array()[0]), 1)

        # backward transform
        alg2 = InverseTransformRasterAlgorithm()
        alg2.initAlgorithm()
        parameters = {
            alg2.P_RASTER: self.filename('transformation.tif'),
            alg2.P_TRANSFORMER: parametersFit[algFit.P_OUTPUT_TRANSFORMER],
            alg2.P_OUTPUT_RASTER: self.filename('inverseTransformation.tif')
        }
        result = self.runalg(alg2, parameters)
        self.assertAlmostEqual(3970.287, np.max(RasterReader(result[alg2.P_OUTPUT_RASTER]).array()[0]), 3)
