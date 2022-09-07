import numpy as np

from enmapbox.exampledata import hires
from enmapboxprocessing.algorithm.createmaskalgorithm import CreateMaskAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestCreateMaskAlgorithm(TestCase):

    def test(self):
        alg = CreateMaskAlgorithm()
        parameters = {
            alg.P_RASTER: hires,
            alg.P_FUNCTION: alg.defaultCodeAsString(),
            alg.P_OUTPUT_RASTER: self.filename('mask.tif'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(6286415, np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array()))
