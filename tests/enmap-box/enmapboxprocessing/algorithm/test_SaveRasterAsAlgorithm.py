import numpy as np

from enmapboxtestdata import enmap, hires
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import QgsRasterLayer


class TestSaveRasterAsAlgorithm(TestCase):

    def test_default(self):
        alg = SaveRasterAsAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        gold = RasterReader(enmap).array()
        lead = RasterReader(result[alg.P_OUTPUT_RASTER]).array()
        self.assertEqual(gold[0].dtype, lead[0].dtype)
        self.assertEqual(np.sum(gold), np.sum(lead))

    def _test_issue814(self):
        alg = SaveRasterAsAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(hires),
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        result = self.runalg(alg, parameters)
        gold = RasterReader(hires).array()
        lead = RasterReader(result[alg.P_OUTPUT_RASTER]).array()
        self.assertEqual(gold[0].dtype, lead[0].dtype)
        self.assertEqual(np.sum(gold), np.sum(lead))
