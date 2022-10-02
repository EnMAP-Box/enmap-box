import numpy as np

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.subsetrasterbandsalgorithm import SubsetRasterBandsAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestSubsetRasterBandsAlgorithm(TestCase):

    def test_default(self):
        alg = SubsetRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_BAND_LIST: [1, 11, 21],
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        result = self.runalg(alg, parameters)
        gold = RasterReader(enmap).array(bandList=[1, 11, 21])
        lead = RasterReader(result[alg.P_OUTPUT_RASTER]).array()
        self.assertEqual(gold[0].dtype, lead[0].dtype)
        self.assertEqual(np.sum(gold), np.sum(lead))

    def _test_issue1349(self):
        filename = self.filename('rasterWithBadBands.tif')
        writer = Driver(filename).createFromArray(np.zeros((2, 10, 10)))
        writer.setBandName('a', 1)
        writer.setBandName('b', 2)
        writer.setBadBandMultiplier(0, 1)
        writer.close()

        alg = SubsetRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: filename,
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        self.assertEqual(reader.bandCount(), 1)
        self.assertEqual(reader.bandName(1), 'b')

    def _test_issue1349_2(self):
        alg = SubsetRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: r'C:\Users\Andreas\Downloads\PRISMA_DESTRIPPED_AOI\PRISMA_DESTRIPPED_AOI.tif',
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        self.assertEqual(reader.bandCount(), 1)
