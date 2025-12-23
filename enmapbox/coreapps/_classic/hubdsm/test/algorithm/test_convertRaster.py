from unittest import TestCase

import numpy as np
from osgeo import gdal

from _classic.hubdsm.algorithm.convertraster import convertRaster
from _classic.hubdsm.algorithm.processingoptions import ProcessingOptions
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.shape import GridShape


class TestConvertRaster(TestCase):

    def test(self):
        mask = Raster.open(MEM_DRIVER.createFromArray(array=np.array([[[1, 0, 1]]])))
        raster = Raster.open(MEM_DRIVER.createFromArray(array=np.array([[[1, 2, 0]]], dtype=np.uint8)))
        assert raster.readAsArray().dtype == np.uint8
        raster = raster.withMask(mask=mask)

        po = ProcessingOptions(shape=GridShape(x=1, y=1))
        converted = convertRaster(raster=raster, noDataValues=[-9999], gdalDataType=gdal.GDT_Float32, po=po)
        assert converted.readAsArray().dtype == np.float32
        assert np.all(np.equal(converted.readAsArray(), [[[1, -9999, 0]]]))
