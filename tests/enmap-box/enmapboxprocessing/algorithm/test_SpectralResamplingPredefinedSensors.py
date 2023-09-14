from enmapboxprocessing.algorithm.spectralresamplingtodesisalgorithm import SpectralResamplingToDesisAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtoenmapalgorithm import SpectralResamplingToEnmapAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat5algorithm import SpectralResamplingToLandsat5Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsat7algorithm import SpectralResamplingToLandsat7Algorithm
from enmapboxprocessing.algorithm.spectralresamplingtolandsatalgorithm import SpectralResamplingToLandsatOliAlgorithm, \
    SpectralResamplingToLandsatEtmAlgorithm, SpectralResamplingToLandsatTmAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtoprismaalgorithm import SpectralResamplingToPrismaAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingtosentinel2algorithm import \
    SpectralResamplingToSentinel2aAlgorithm, SpectralResamplingToSentinel2bAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import enmap
from qgis.core import QgsRasterLayer


class TestSpectralResamplingPredefinedSensors(TestCase):

    def test_desis(self):
        alg = SpectralResamplingToDesisAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled3.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(235, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_enmap(self):
        alg = SpectralResamplingToEnmapAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(224, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_prisma(self):
        alg = SpectralResamplingToPrismaAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled2.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(234, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_sentinel2a(self):
        alg = SpectralResamplingToSentinel2aAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(13, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_sentinel2b(self):
        alg = SpectralResamplingToSentinel2bAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(13, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_landsatOli(self):
        alg = SpectralResamplingToLandsatOliAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(6, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_landsatEtm(self):
        alg = SpectralResamplingToLandsatEtmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(6, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_landsatTm(self):
        alg = SpectralResamplingToLandsatTmAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: self.filename('resampled.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(6, QgsRasterLayer(parameters[alg.P_OUTPUT_RASTER]).bandCount())
