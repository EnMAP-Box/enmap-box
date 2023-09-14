import numpy as np

from enmapboxprocessing.algorithm.spectralresamplingbywavelengthandfwhmalgorithm import \
    SpectralResamplingByWavelengthAndFwhmAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap, envi_library_berlin_sli, enmap_berlin_srf_csv


class TestSpectralResamplingByWavelengthAndFwhmAlgorithm(TestCase):

    def test_fromRaster(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: enmap,
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromEnviSpeclib(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: envi_library_berlin_sli,
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromEnviSpeclibHeader(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: envi_library_berlin_sli.replace('.sli', '.hdr'),
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromEnviRasterHeader(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: enmap.replace('.bsq', '.hdr'),
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromCsvTable(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: enmap_berlin_srf_csv,
            alg.P_SAVE_RESPONSE_FUNCTION: True,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
