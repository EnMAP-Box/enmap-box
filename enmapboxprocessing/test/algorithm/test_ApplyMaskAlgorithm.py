import numpy as np

from enmapbox.exampledata import enmap, landcover_polygon
from enmapboxprocessing.algorithm.applymaskalgorithm import ApplyMaskAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestLayerToMaskAlgorithm(TestCase):

    def test_raster(self):
        alg = ApplyMaskAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_MASK: landcover_polygon,
            alg.P_OUTPUT_RASTER: self.filename('masked.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(-7549619, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1])))
