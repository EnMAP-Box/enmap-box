from unittest import TestCase

import numpy as np

from _classic.hubdsm.core.band import Band
from _classic.hubdsm.core.mask import Mask
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER

outdir = r'c:\unittests\hubdsm'


class TestMask(TestCase):

    def test_readAsArray(self):
        # mask without noDataValue behaves like a binary 0/1 mask
        band = Band.fromGdalBand(MEM_DRIVER.createFromArray(array=np.array([[[-1, 0, 1]]])).band(1))
        mask = Mask(band=band)
        self.assertTrue(np.all(np.equal(mask.readAsArray(), [True, False, True])))
        # mask with noDataValue maps the noDataValue to False and all other values to True
        band.gdalBand.setNoDataValue(-1)
        self.assertTrue(np.all(np.equal(mask.readAsArray(), [False, True, True])))
        # masks can be inverted
        mask = mask.withInvert(invert=True)
        self.assertTrue(np.all(np.equal(mask.readAsArray(), [True, False, False])))
