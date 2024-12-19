import unittest

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.layertomaskalgorithm import LayerToMaskAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap, landcover_polygon


# skip in gdal 3.10, because of
# '" ERROR 1: Failed to parse \'220.0\' as decimal integer: pattern \'220.0\' does not match to the end"'
@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestLayerToMaskAlgorithm(TestCase):

    @unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
    def test_raster(self):
        alg = LayerToMaskAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_LAYER: enmap,
            alg.P_OUTPUT_MASK: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(71158, np.sum(RasterReader(result[alg.P_OUTPUT_MASK]).array()))

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
