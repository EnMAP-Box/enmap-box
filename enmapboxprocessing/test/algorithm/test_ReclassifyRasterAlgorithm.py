import numpy as np

from enmapboxprocessing.algorithm.reclassifyrasteralgorithm import ReclassifyRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import landcover_raster_30m
from qgis.core import QgsRasterLayer


class TestReclassifyRasterAlgorithm(TestCase):

    def test_withCategories(self):
        alg = ReclassifyRasterAlgorithm()
        parameters = {
            alg.P_RASTER: landcover_raster_30m,
            alg.P_MAPPING: "{1: 1, 2: 1, 3: 2, 4: 2, 6: 3}",
            alg.P_CATEGORIES: "[(1, 'urban', '#e60000'), (2, 'vegetation', '#98e600'), (3, 'water', '#0064ff')]",
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif')
        }
        self.runalg(alg, parameters)
        layer = QgsRasterLayer(parameters[alg.P_OUTPUT_CLASSIFICATION])
        self.assertEqual(
            [Category(value=1, name='urban', color='#e60000'), Category(value=2, name='vegetation', color='#98e600'),
             Category(value=3, name='water', color='#0064ff')],
            Utils.categoriesFromRenderer(layer.renderer()),
        )
        self.assertEqual(2910, np.sum(RasterReader(parameters[alg.P_OUTPUT_CLASSIFICATION]).array()))

    def test_withoutCategories(self):
        alg = ReclassifyRasterAlgorithm()
        parameters = {
            alg.P_RASTER: landcover_raster_30m,
            alg.P_MAPPING: "{1: 1, 2: 1, 3: 2, 4: 2, 6: 3}",
            alg.P_OUTPUT_CLASSIFICATION: self.filename('classification.tif')
        }
        self.runalg(alg, parameters)
        self.assertEqual(2910, np.sum(RasterReader(parameters[alg.P_OUTPUT_CLASSIFICATION]).array()))
