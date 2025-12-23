from unittest.case import TestCase

import numpy as np
from osgeo import gdal

from enmapbox.exampledata import enmap
from _classic.hubdsm.core.band import Band
from _classic.hubdsm.core.mask import Mask
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER


class TestBand(TestCase):

    def test_Band(self):
        band = Band(name='enmap', filename=enmap, number=1, mask=None, _gdalBand=None)
        assert isinstance(band.gdalBand.gdalBand, gdal.Band)

    def test_readAsArray(self):
        mask = Mask(band=Band.fromGdalBand(MEM_DRIVER.createFromArray(array=np.array([[[1, 1, 1, 0, 0, 0]]])).band(1)))
        band = Band.fromGdalBand(MEM_DRIVER.createFromArray(array=np.array([[[-1, 0, 1, -1, 0, 1]]])).band(1))
        band.gdalBand.setNoDataValue(-1)
        band = band.withMask(mask=mask)
        assert np.all(np.equal(band.readAsArray(), [[-1, 0, 1, -1, 0, 1]]))
        assert np.all(np.equal(mask.readAsArray(), [[True, True, True, False, False, False]]))
        assert np.all(np.equal(band.readAsMaskArray(), [[False, True, True, False, False, False]]))

    def test_readAsMaskArray(self):
        band = Band.fromGdalBand(MEM_DRIVER.createFromArray(array=np.array([[[np.nan, 0, 1]]])).band(1))
        band.gdalBand.setNoDataValue(np.nan)
        assert np.all(np.equal(band.readAsMaskArray(), [[False, True, True]]))

