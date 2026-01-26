from unittest import TestCase

import numpy as np

from _classic.hubdsm.algorithm.aggregatebands import aggregateBands
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER
from _classic.hubdsm.core.raster import Raster


class TestAggregateBands(TestCase):

    def test(self):
        raster = Raster.open(MEM_DRIVER.createFromArray(array=np.array([[[1]], [[2]], [[3]]], dtype=np.uint8)))
        raster2 = aggregateBands(raster=raster, aggregationFunction=np.mean)
        self.assertEqual(raster2.readAsArray(), 2.)
        raster2 = aggregateBands(raster=raster, aggregationFunction=np.min)
        self.assertEqual(raster2.readAsArray(), 1.)
        raster2 = aggregateBands(raster=raster, aggregationFunction=np.max)
        self.assertEqual(raster2.readAsArray(), 3.)
        raster2 = aggregateBands(raster=raster, aggregationFunction=np.any)
        self.assertEqual(raster2.readAsArray(), 1)

