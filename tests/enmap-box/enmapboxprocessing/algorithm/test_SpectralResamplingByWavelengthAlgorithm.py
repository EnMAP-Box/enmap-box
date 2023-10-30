import numpy as np

from enmapboxprocessing.algorithm.spectralresamplingbywavelengthalgorithm import SpectralResamplingByWavelengthAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from tests.enmapboxtestdata import enmap, envi_library_berlin_sli, enmap_berlin_srf_csv, classificationDatasetAsPklFile, \
    enmap_potsdam


class TestSpectralResamplingByWavelengthAlgorithm(TestCase):

    def test_fromSameRaster(self):  # this is an edge case
        alg = SpectralResamplingByWavelengthAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WAVELENGTH_FILE: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29424494, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromDifferentRaster(self):
        alg = SpectralResamplingByWavelengthAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WAVELENGTH_FILE: enmap_potsdam,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(133921411, np.round(np.sum(reader.array()[100])))
        self.assertEqual(14, np.sum([reader.badBandMultiplier(bandNo) == 0 for bandNo in reader.bandNumbers()]))

    def test_fromEnviSpeclib(self):
        alg = SpectralResamplingByWavelengthAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WAVELENGTH_FILE: envi_library_berlin_sli,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29424494, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromEnviSpeclibHeader(self):
        alg = SpectralResamplingByWavelengthAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WAVELENGTH_FILE: envi_library_berlin_sli.replace('.sli', '.hdr'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29424494, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromEnviRasterHeader(self):
        alg = SpectralResamplingByWavelengthAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WAVELENGTH_FILE: enmap.replace('.bsq', '.hdr'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29424494, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_fromCsvTable(self):
        alg = SpectralResamplingByWavelengthAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WAVELENGTH_FILE: enmap_berlin_srf_csv,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29424494, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

    def test_wrongResponseFile(self):
        alg = SpectralResamplingByWavelengthAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WAVELENGTH_FILE: classificationDatasetAsPklFile,  # PKL files aren't valid response files
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        try:
            self.runalg(alg, parameters)
            assert 0, 'error not raised, something went wrong'
        except Exception as error:
            pass
