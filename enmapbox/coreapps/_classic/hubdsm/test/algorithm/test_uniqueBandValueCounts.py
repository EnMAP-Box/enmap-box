from unittest import TestCase
from unittest.case import TestCase

import numpy as np

from _classic.hubdsm.algorithm.processingoptions import ProcessingOptions
from _classic.hubdsm.algorithm.uniquebandvaluecounts import uniqueBandValueCounts
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.shape import GridShape


class TestUniqueBandValueCounts(TestCase):

    def test(self):
        mask = Raster.open(MEM_DRIVER.createFromArray(array=np.array([[[1, 1, 1, 1, 1, 0, 0, 0, 0, 0]]])))
        raster = Raster.open(
            MEM_DRIVER.createFromArray(array=np.array([[[-1, 0, 2, 2, 30, -1, 0, 2, 2, 30]]]))
        ).withMask(mask=mask)
        band = raster.band(number=1)
        lead = uniqueBandValueCounts(band=band, po=ProcessingOptions(shape=GridShape(y=100, x=999999999999)))
        gold = {-1: 1, 0: 1, 2: 2, 30: 1}
        self.assertDictEqual(gold, lead)

        band.gdalBand.setNoDataValue(-1)
        lead = uniqueBandValueCounts(band=band)
        gold = {0: 1, 2: 2, 30: 1}
        self.assertDictEqual(gold, lead)