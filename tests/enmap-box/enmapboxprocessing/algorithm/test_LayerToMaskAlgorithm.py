import unittest

import numpy as np
from osgeo import gdal_version

from enmapboxtestdata import enmap, landcover_polygon
from enmapboxprocessing.algorithm.layertomaskalgorithm import LayerToMaskAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader


class TestLayerToMaskAlgorithm(TestCase):

    def test_raster(self):
        alg = LayerToMaskAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_LAYER: enmap,
            alg.P_OUTPUT_MASK: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(71158, np.sum(RasterReader(result[alg.P_OUTPUT_MASK]).array()))

    # skip in gdal 3.10, because of
    # '" ERROR 1: Failed to parse \'220.0\' as decimal integer: pattern \'220.0\' does not match to the end"'
    @unittest.skipIf(gdal_version == (3, 10),
                     'Rasterize decimal error')
    def test_vector(self):
        alg = LayerToMaskAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_LAYER: landcover_polygon,
            alg.P_GRID: enmap,
            alg.P_OUTPUT_MASK: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2028, np.sum(RasterReader(result[alg.P_OUTPUT_MASK]).array()))
