from unittest.case import TestCase

import numpy as np

from _classic.hubdsm.core.gdaldriver import MEM_DRIVER
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.rastercollection import RasterCollection


class TestRasterCollection(TestCase):

    def test_readAsSample(self):
        r1 = Raster.createFromArray(array=np.zeros((3, 2, 2))).withName('Raster1').rename(['B11', 'B12', 'B13'])
        r2 = Raster.createFromArray(array=np.ones((2, 2, 2))).withName('Raster2').rename(['B21', 'B22'])
        c = RasterCollection(rasters=(r1, r2))
        samples, location = c.readAsSample(xMap='xMap', yMap='yMap')
        self.assertTrue(np.all(np.equal(samples['Raster1'].array(), np.zeros((3, 4)))))
        self.assertTrue(np.all(np.equal(samples['Raster2'].array(), np.ones((2, 4)))))
