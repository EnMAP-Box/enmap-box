import numpy as np

from enmapboxtestdata import enmap, enmap_srf_library
from enmapboxprocessing.algorithm.spectralresamplingbyresponsefunctionlibraryalgorithm import \
    SpectralResamplingByResponseFunctionLibraryAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader


class TestSpectralResamplingByResponseFunctionLibraryAlgorithmBase(TestCase):

    def test(self):
        alg = SpectralResamplingByResponseFunctionLibraryAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_LIBRARY: enmap_srf_library,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(14908146678, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))
