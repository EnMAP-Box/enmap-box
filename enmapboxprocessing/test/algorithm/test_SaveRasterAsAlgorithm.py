import numpy as np

from enmapbox.exampledata import enmap, hires
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.core import QgsRasterLayer


class TestTranslateAlgorithm(TestCase):

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

    def test_issue814(self):
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
