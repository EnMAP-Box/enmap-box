import numpy as np

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.spectralresamplingtodesisalgorithm import SpectralResamplingToDesisAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtoenmapalgorithm import SpectralResamplingToEnmapAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat5algorithm import SpectralResamplingToLandsat5Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat7algorithm import SpectralResamplingToLandsat7Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat8algorithm import SpectralResamplingToLandsat8Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtoprismaalgorithm import SpectralResamplingToPrismaAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtosentinel2algorithm import SpectralResamplingToSentinel2Algorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestSpectralResamplingByResponseFunctionConvolutionAlgorithmBase(TestCase):

    def test_fullyDefinedResponseFunction(self):
        alg = SpectralResamplingToLandsat8Algorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(30542976, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fwhm(self):
        alg = SpectralResamplingToEnmapAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_all(self):
        algs = [SpectralResamplingToPrismaAlgorithm(),
                SpectralResamplingToDesisAlgorithm(),
                SpectralResamplingToEnmapAlgorithm(),
                SpectralResamplingToSentinel2Algorithm(),
                SpectralResamplingToLandsat5Algorithm(),
                SpectralResamplingToLandsat7Algorithm(),
                SpectralResamplingToLandsat8Algorithm()]
        for alg in algs:
            parameters = {
                alg.P_RASTER: enmap,
                alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
            }
            print(alg.displayName())
            self.runalg(alg, parameters)
