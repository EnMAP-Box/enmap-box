import numpy as np

from enmapboxtestdata import enmap
from enmapboxprocessing.algorithm.spectralresamplingtodesisalgorithm import SpectralResamplingToDesisAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtoenmapalgorithm import SpectralResamplingToEnmapAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat5algorithm import SpectralResamplingToLandsat5Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat7algorithm import SpectralResamplingToLandsat7Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat8algorithm import SpectralResamplingToLandsat8Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtoprismaalgorithm import SpectralResamplingToPrismaAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtosentinel2algorithm import SpectralResamplingToSentinel2Algorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader


class TestSpectralResamplingByResponseFunctionConvolutionAlgorithmBase(TestCase):

    def test_fullyDefinedResponseFunction(self):
        alg = SpectralResamplingToLandsat8Algorithm()
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
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(140855227, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

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

    def _test_issue490(self):
        alg = SpectralResamplingToLandsat5Algorithm()
        parameters = {
            alg.P_RASTER: r'D:\data\sensors\enmap\ENMAP01-____L2A-DT0000004135_20221005T023547Z_010_V010106_20221014T102749Z\ENMAP01-____L2A-DT0000004135_20221005T023547Z_010_V010106_20221014T102749Z-SPECTRAL_IMAGE.vrt',
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        print(alg.displayName())
        self.runalg(alg, parameters)
