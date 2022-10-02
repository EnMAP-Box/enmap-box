import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.importprismal2dalgorithm import ImportPrismaL2DAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportPrismaL2DAlgorithm(TestCase):

    def test(self):

        alg = ImportPrismaL2DAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\prisma\PRS_L2D_STD_20201107101404_20201107101408_0001.he5',
            alg.P_OUTPUT_SPECTRAL_CUBE: self.filename('prismaL2D_SPECTRAL.tif'),
            alg.P_OUTPUT_SPECTRAL_GEOLOCATION: self.filename('prismaL2D_SPECTRAL_GEOLOCATION.vrt'),
            alg.P_OUTPUT_SPECTRAL_GEOMETRIC: self.filename('prismaL2D_SPECTRAL_GEOMETRIC.vrt'),
            alg.P_OUTPUT_SPECTRAL_ERROR: self.filename('prismaL2D_SPECTRAL_ERROR.tif'),

            alg.P_OUTPUT_PAN_CUBE: self.filename('prismaL2D_PAN.vrt'),
            alg.P_OUTPUT_PAN_GEOLOCATION: self.filename('prismaL2D_PAN_GEOLOCATION.vrt'),
            alg.P_OUTPUT_PAN_ERROR: self.filename('prismaL2D_PAN_ERROR.vrt'),

        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(234, RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE]).bandCount())
        self.assertAlmostEqual(0.066, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE]).array()), 3)

        self.assertEqual(2, RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOLOCATION]).bandCount())
        self.assertAlmostEqual(32.920, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOLOCATION]).array()), 3)

        self.assertEqual(3, RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOMETRIC]).bandCount())
        self.assertAlmostEqual(31.597, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOMETRIC]).array()), 3)

        self.assertEqual(234, RasterReader(result[alg.P_OUTPUT_SPECTRAL_ERROR]).bandCount())
        self.assertAlmostEqual(0.032, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_ERROR]).array()), 3)

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_PAN_CUBE]).bandCount())
        self.assertAlmostEqual(0.219, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_CUBE]).array()), 3)

        self.assertEqual(2, RasterReader(result[alg.P_OUTPUT_PAN_GEOLOCATION]).bandCount())
        self.assertAlmostEqual(32.920, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_GEOLOCATION]).array()), 3)

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_PAN_ERROR]).bandCount())
        self.assertAlmostEqual(0.003, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_ERROR]).array()), 3)

    def test_badBandThresholding1(self):

        alg = ImportPrismaL2DAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\prisma\PRS_L2D_STD_20201107101404_20201107101408_0001.he5',
            alg.P_BAD_BAND_THRESHOLD: 0.1,
            alg.P_BAD_PIXEL_TYPE: [alg.InvalidL1Pixel],
            alg.P_OUTPUT_SPECTRAL_CUBE: self.filename('prismaL2D_SPECTRAL.tif'),
            alg.P_OUTPUT_SPECTRAL_ERROR: self.filename('prismaL2D_SPECTRAL_ERROR.tif'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE])
        bbl = [reader.badBandMultiplier(bandNo) for bandNo in reader.bandNumbers()]
        self.assertEqual(215, sum(bbl))

    def test_badBandThresholding2(self):
        alg = ImportPrismaL2DAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\prisma\PRS_L2D_STD_20201107101404_20201107101408_0001.he5',
            alg.P_BAD_BAND_THRESHOLD: 0.1,
            alg.P_BAD_PIXEL_TYPE: [alg.InvalidL1Pixel, alg.NegativeAtmosphericCorrectionPixel,
                                   alg.SaturatedAtmosphericCorrectionPixel],
            alg.P_OUTPUT_SPECTRAL_CUBE: self.filename('prismaL2D_SPECTRAL.tif'),
            alg.P_OUTPUT_SPECTRAL_ERROR: self.filename('prismaL2D_SPECTRAL_ERROR.tif'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE])
        bbl = [reader.badBandMultiplier(bandNo) for bandNo in reader.bandNumbers()]
        self.assertEqual(212, sum(bbl))

    def _test_issue1318(self):
        alg = ImportPrismaL2DAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\prisma\PRS_L2D_STD_20201107101404_20201107101408_0001.he5',
            alg.P_OUTPUT_SPECTRAL_CUBE: self.filename('prismaL2D_SPECTRAL.bsq')
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE])
        driver: gdal.Driver = reader.gdalDataset.GetDriver()
        self.assertEqual('ENVI', driver.ShortName)
