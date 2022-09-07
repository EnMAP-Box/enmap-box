import numpy as np

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.spectralresamplingbyspectralrasterwavelengthandfwhmalgorithm import \
    SpectralResamplingBySpectralRasterWavelengthAndFwhmAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestSpectralResamplingByResponseFunctionLibraryAlgorithmBase(TestCase):

    def test(self):
        alg = SpectralResamplingBySpectralRasterWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_RASTER: enmap,
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
