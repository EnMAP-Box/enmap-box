import numpy as np

from enmapboxprocessing.algorithm.spectralresamplingbyresponsefunctionlibraryalgorithm import \
    SpectralResamplingByResponseFunctionLibraryAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap, enmap_srf_library


class TestSpectralResamplingByResponseFunctionLibraryAlgorithm(TestCase):

    def test(self):
        alg = SpectralResamplingByResponseFunctionLibraryAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_LIBRARY: enmap_srf_library,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(14908146452, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(), dtype=float))
