from unittest.case import TestCase

import numpy as np

from enmapbox.exampledata import enmap
from _classic.hubdsm.core.error import ProjectionMismatchError
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER, GdalDriver


class TestGdalRaster(TestCase):

    def test(self):
        gdalRaster = GdalRaster.open(enmap)
        self.assertEqual(gdalRaster.filename, enmap)
        self.assertEqual(gdalRaster.filenames[0], enmap)
        self.assertEqual(gdalRaster.driver, GdalDriver(name='ENVI'))
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1]]]))
        self.assertEqual(gdalRaster.filenames, [])

    def test_flushCache(self):
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1]], [[0]]]))
        gdalRaster.flushCache()

    def test_readAsArray(self):
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1, 2]]]))
        self.assertTrue(np.all(np.equal(gdalRaster.readAsArray(), [[[1, 2]]])))
        self.assertTrue(np.all(np.equal(gdalRaster.readAsArray(), gdalRaster.readAsArray(grid=gdalRaster.grid))))
        try:
            grid = GdalRaster.open(enmap).grid
            gdalRaster.readAsArray(grid=grid)
        except ProjectionMismatchError:
            pass

    def test_metadata(self):
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1, 2]]]))
        gdalRaster.setMetadataDict(metadataDict={'A': {'a': 1}, 'B': {'b': None}})
        self.assertDictEqual(gdalRaster.metadataDict['A'], {'a': '1'})
        self.assertIsNone(gdalRaster.metadataItem(key='b', domain='B'))
        gdalRaster.setMetadataDict(metadataDict={})

    def test_grid(self):
        gdalRaster = GdalRaster.open(enmap)
        gdalRaster2 = MEM_DRIVER.createFromArray(array=gdalRaster.readAsArray())
        self.assertFalse(gdalRaster.grid.equal(other=gdalRaster2.grid))
        gdalRaster2.setGrid(grid=gdalRaster.grid)
        self.assertTrue(gdalRaster.grid.equal(other=gdalRaster2.grid))

    def test_translate(self):
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1, 2]]]))
        gdalRaster2 = gdalRaster.translate()
        self.assertTrue(np.all(np.equal(gdalRaster2.readAsArray(), [[[1, 2]]])))
