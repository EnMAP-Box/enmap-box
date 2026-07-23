from unittest import TestCase

import numpy as np
from osgeo import gdal

from _classic.hubdsm.algorithm.saveasenvi import saveAsEnvi
from _classic.hubdsm.algorithm.processingoptions import ProcessingOptions
from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.shape import GridShape


class TestSaveAsEnvi(TestCase):

    def test_spectralRaster(self):
        array = np.array([[[0]], [[1]], [[10]]])
        gdalRaster = GdalRaster.createFromArray(array=array)
        gdalRaster.setMetadataItem(key='wavelength', value=[1, 2, 3], domain='ENVI')
        gdalRaster.setMetadataItem(key='wavelength_units', value='nanometers', domain='ENVI')
        gdalRaster.setMetadataItem(key='myKey', value='hello', domain='ENVI')
        gdalRaster.setNoDataValue(value=-9999)
        categories = [
            Category(id=1, name='class 1', color=Color(255, 0, 0)),
            Category(id=10, name='class 10', color=Color(0, 255, 0))
        ]
        gdalRaster.setCategories(categories=categories)
        for gdalBand, name in zip(gdalRaster.bands, ['b1', 'b2', 'b3']):
            gdalBand.setDescription(name)

        gdalRaster2 = saveAsEnvi(gdalRaster=gdalRaster, filename='c:/vsimem/raster.xyz')
        self.assertTrue(np.all(array == gdalRaster2.readAsArray()))
        self.assertListEqual([1, 2, 3], gdalRaster2.metadataItem(key='wavelength', domain='ENVI', dtype=int))
        self.assertEqual('nanometers', gdalRaster2.metadataItem(key='wavelength units', domain='ENVI'))
        self.assertEqual('bsq', gdalRaster2.metadataItem(key='interleave', domain='ENVI'))
        self.assertEqual('hello', gdalRaster2.metadataItem(key='myKey', domain='ENVI'))
        self.assertEqual(-9999, gdalRaster2.band(1).noDataValue)
        self.assertListEqual(categories, gdalRaster2.categories)
