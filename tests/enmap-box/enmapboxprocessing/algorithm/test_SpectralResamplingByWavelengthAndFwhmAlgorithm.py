import numpy as np

from enmapboxprocessing.algorithm.spectralresamplingbywavelengthandfwhmalgorithm import \
    SpectralResamplingByWavelengthAndFwhmAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap, envi_library_berlin_sli, enmap_berlin_srf_csv, classificationDatasetAsPklFile, \
    enmap_potsdam


class TestSpectralResamplingByWavelengthAndFwhmAlgorithm(TestCase):

    def test_fromRaster(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: enmap,
            alg.P_OUTPUT_LIBRARY: self.filename('srf.geojson'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        try:
            self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
        except AssertionError:
            # also check for another checksum, because of a GDAL bug
            self.assertEqual(29439318, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))

        srf = Utils().jsonLoad(result[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(177, len(srf['features']))

    def test_fromEnviSpeclib(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: envi_library_berlin_sli,
            alg.P_OUTPUT_LIBRARY: self.filename('srf.geojson'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
        srf = Utils().jsonLoad(result[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(177, len(srf['features']))
        srf = Utils().jsonLoad(result[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(177, len(srf['features']))

    def test_fromEnviSpeclibHeader(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: envi_library_berlin_sli.replace('.sli', '.hdr'),
            alg.P_OUTPUT_LIBRARY: self.filename('srf.geojson'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
        srf = Utils().jsonLoad(result[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(177, len(srf['features']))

    def test_fromEnviRasterHeader(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: enmap.replace('.bsq', '.hdr'),
            alg.P_OUTPUT_LIBRARY: self.filename('srf.geojson'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
        srf = Utils().jsonLoad(result[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(177, len(srf['features']))

    def test_fromCsvTable(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: enmap_berlin_srf_csv,
            alg.P_OUTPUT_LIBRARY: self.filename('srf.geojson'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(29437304, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
        srf = Utils().jsonLoad(result[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(177, len(srf['features']))

    def test_wrongResponseFile(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_RESPONSE_FILE: classificationDatasetAsPklFile,  # PKL files aren't valid response files
            alg.P_OUTPUT_LIBRARY: self.filename('srf.geojson'),
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        try:
            self.runalg(alg, parameters)
            assert 0, 'error not raised, something went wrong'
        except Exception as error:
            pass

    def test_userFwhm(self):
        alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap_potsdam,
            alg.P_RESPONSE_FILE: enmap_potsdam,
            alg.P_FWHM: 10,
            alg.P_OUTPUT_LIBRARY: self.filename('srf.geojson'),
            alg.P_OUTPUT_RASTER: self.filename('resampled_10.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(-36108144.0, np.round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0])))
        srf = Utils().jsonLoad(result[alg.P_OUTPUT_LIBRARY])
        self.assertEqual(224, len(srf['features']))
