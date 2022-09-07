import numpy as np

from enmapboxprocessing.algorithm.createdefaultpalettedrasterrendereralgorithm import \
    CreateDefaultPalettedRasterRendererAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.core import QgsRasterLayer


class TestCreateDefaultPalettedRasterRendererAlgorithm(TestCase):

    def test(self):
        filename = self.filename('raster.tif')
        Driver(filename).createFromArray(array=np.array([[[1, 2, 3]]]))

        alg = CreateDefaultPalettedRasterRendererAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: filename,
            alg.P_BAND: 1,
            alg.P_CATEGORIES: "(1, 'C1', '#FF0000')\n, (2, 'C2', '#00FF00')"
        }
        self.runalg(alg, parameters)
        raster = QgsRasterLayer(filename)
        renderer = raster.renderer()
        categories = Utils.categoriesFromPalettedRasterRenderer(renderer)
        gold = [Category(value=1, name='C1', color='#ff0000'), Category(value=2, name='C2', color='#00ff00')]
        self.assertListEqual(gold, categories)
