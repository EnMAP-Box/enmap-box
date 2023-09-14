import numpy as np

from enmapboxprocessing.algorithm.spectralresamplingtoenmapalgorithm import SpectralResamplingToEnmapAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsatalgorithm import SpectralResamplingToLandsatOliAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap


class TestSpectralResamplingByResponseFunctionConvolutionAlgorithmBase(TestCase):

    def test_fullyDefinedResponseFunction(self):
        alg = SpectralResamplingToLandsatOliAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(30542975, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_responseFunctionByFwhm(self):
        alg = SpectralResamplingToEnmapAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(-8712000, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
