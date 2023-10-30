from math import inf, nan

import numpy as np

from enmapboxprocessing.algorithm.subsetrasterbandsalgorithm import SubsetRasterBandsAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap, enmap_potsdam


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

    def test_excludeBadBands(self):
        alg = SubsetRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: enmap_potsdam,
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        self.assertEqual(218, RasterReader(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_excludeDerivedBadBands(self):
        array = [[[1, 1, 1]], [[inf, nan, -99]]]

        writer = self.rasterFromArray(array)
        writer.setNoDataValue(-99)
        writer.close()

        alg = SubsetRasterBandsAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_EXCLUDE_DERIVED_BAD_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        self.assertEqual(3, np.sum(RasterReader(parameters[alg.P_OUTPUT_RASTER]).array()))
