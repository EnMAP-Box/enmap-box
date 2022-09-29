import numpy as np

from enmapboxprocessing.algorithm.importprismal1algorithm import ImportPrismaL1Algorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportPrismaL1Algorithm(TestCase):

    def test(self):
        alg = ImportPrismaL1Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\prisma\PRS_L1_STD_OFFL_20201107101404_20201107101408_0001.he5',
            alg.P_OUTPUT_SPECTRAL_CUBE: self.filename('prismaL1_SPECTRAL.tif'),
            alg.P_OUTPUT_PAN_CUBE: self.filename('prismaL1_PAN.vrt'),
            alg.P_OUTPUT_CLOUD_MASK: self.filename('prismaL1_CLOUD_MASK.vrt'),
            alg.P_OUTPUT_LANDCOVER_MASK: self.filename('prismaL1_LANDCOVER_MASK.vrt'),
            alg.P_OUTPUT_SUN_GLINT_MASK: self.filename('prismaL1_SUN_GLINT_MASK.vrt'),
            alg.P_OUTPUT_SPECTRAL_GEOLOCATION: self.filename('prismaL1_SPECTRAL_GEOLOCATION.vrt'),
            alg.P_OUTPUT_SPECTRAL_ERROR: self.filename('prismaL1_SPECTRAL_ERROR.tif'),
            alg.P_OUTPUT_PAN_GEOLOCATION: self.filename('prismaL1_PAN_GEOLOCATION.vrt'),
            alg.P_OUTPUT_PAN_ERROR: self.filename('prismaL1_PAN_ERROR.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)

        self.assertEqual(234, RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE]).bandCount())
        self.assertAlmostEqual(804.056, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE]).array()), 3)

        self.assertEqual(2, RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOLOCATION]).bandCount())
        self.assertAlmostEqual(32.920, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOLOCATION]).array()), 3)

        self.assertEqual(234, RasterReader(result[alg.P_OUTPUT_SPECTRAL_ERROR]).bandCount())
        self.assertAlmostEqual(0.013, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_ERROR]).array()), 3)

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_PAN_CUBE]).bandCount())
        self.assertAlmostEqual(65.661, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_CUBE]).array()), 3)

        self.assertEqual(2, RasterReader(result[alg.P_OUTPUT_PAN_GEOLOCATION]).bandCount())
        self.assertAlmostEqual(32.920, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_GEOLOCATION]).array()), 3)

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_PAN_ERROR]).bandCount())
        self.assertAlmostEqual(0.000, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_ERROR]).array()), 3)

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_CLOUD_MASK]).bandCount())
        self.assertEqual(255, np.max(RasterReader(result[alg.P_OUTPUT_CLOUD_MASK]).array()))

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_LANDCOVER_MASK]).bandCount())
        self.assertEqual(255, np.max(RasterReader(result[alg.P_OUTPUT_LANDCOVER_MASK]).array()))

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_SUN_GLINT_MASK]).bandCount())
        self.assertEqual(255, np.max(RasterReader(result[alg.P_OUTPUT_SUN_GLINT_MASK]).array()))
