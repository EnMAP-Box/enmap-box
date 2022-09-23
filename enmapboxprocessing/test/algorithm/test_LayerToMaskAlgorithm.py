import numpy as np

from enmapbox.exampledata import enmap, landcover_polygon
from enmapboxprocessing.algorithm.layertomaskalgorithm import LayerToMaskAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


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
