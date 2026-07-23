from os.path import exists
from unittest import TestCase

import numpy as np

from _classic.hubdsm.core.gdaldriver import (GdalDriver, MEM_DRIVER, ENVI_BSQ_DRIVER, ENVI_BIL_DRIVER,
                                    ENVI_BIP_DRIVER, GTIFF_DRIVER, ERDAS_DRIVER, VRT_DRIVER)


class TestGdalDriver(TestCase):

    def test(self):
        driver = GdalDriver(name='MEM')

    def test_fromFilename(self):
        settings = [([None, ''], MEM_DRIVER),
                    (['a.bsq', 'a.sli', 'a.esl'], ENVI_BSQ_DRIVER),
                    (['a.bil'], ENVI_BIL_DRIVER),
                    (['a.bip'], ENVI_BIP_DRIVER),
                    (['a.tif', 'a.tiff'], GTIFF_DRIVER),
                    (['a.img'], ERDAS_DRIVER),
                    (['a.vrt'], VRT_DRIVER),
                    (['a.xyz'], ENVI_BSQ_DRIVER)]

        for filenames, driver in settings:
            for filename in filenames:
                self.assertEqual(GdalDriver.fromFilename(filename=filename), driver)

    def test_create(self):
        MEM_DRIVER.createFromArray(array=np.array([[[1]]], dtype=np.uint8))

    def test_delete(self):
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[1]]]))
        MEM_DRIVER.delete(gdalRaster.filename)
        gdalRaster = GTIFF_DRIVER.createFromArray(array=np.array([[[1]]]), filename='/vsimem/tmp.tif')
        GTIFF_DRIVER.delete(gdalRaster.filename)
        gdalRaster = GTIFF_DRIVER.createFromArray(array=np.array([[[1]]]), filename='tmp.tif')
        del gdalRaster
        GTIFF_DRIVER.delete('tmp.tif')
        self.assertFalse(exists('tmp.tif'))

    def test_prepareCreation(self):
        MEM_DRIVER.prepareCreation(filename=None)
        MEM_DRIVER.prepareCreation(filename='will be ignored.bsq')
        GTIFF_DRIVER.prepareCreation(filename='/vsimem/tmp.tif')
        GTIFF_DRIVER.prepareCreation(filename='tmp.tif')
