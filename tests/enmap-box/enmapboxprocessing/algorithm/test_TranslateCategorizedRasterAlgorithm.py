import numpy as np

from enmapboxtestdata import enmap
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.translatecategorizedrasteralgorithm import TranslateCategorizedRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import landcover_polygon_30m_epsg3035
from qgis.core import QgsRasterLayer


class TestTranslateCategorizedRasterAlgorithm(TestCase):

    def test_default(self):
        alg = TranslateCategorizedRasterAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_RASTER: QgsRasterLayer(landcover_polygon_30m_epsg3035),
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTPUT_CATEGORIZED_RASTER: self.filename('landcover.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(5126, np.sum(RasterReader(result[alg.P_OUTPUT_CATEGORIZED_RASTER]).array()))
