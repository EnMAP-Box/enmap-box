from os.path import exists
from unittest import TestCase

import numpy as np

from _classic.hubdsm.core.ogrdriver import (OgrDriver, MEMORY_DRIVER, SHAPEFILE_DRIVER, GEOPACKAGE_DRIVER)
from _classic.hubdsm.core.ogrvector import OgrVector


class TestOgrDriver(TestCase):

    def test(self):
        driver = OgrDriver(name='MEMORY')

    def test_fromFilename(self):
        settings = [([None, ''], MEMORY_DRIVER),
                    (['a.shp'], SHAPEFILE_DRIVER),
                    (['a.gpkg'], GEOPACKAGE_DRIVER)]
        for filenames, driver in settings:
            for filename in filenames:
                self.assertEqual(OgrDriver.fromFilename(filename=filename), driver)

    def test_createVector(self):
        ogrVector = MEMORY_DRIVER.createVector()
        self.assertIsInstance(ogrVector, OgrVector)

    def test_delete(self):
        ogrVector = MEMORY_DRIVER.createVector()
        MEMORY_DRIVER.delete(ogrVector.filename)
        ogrVector = GEOPACKAGE_DRIVER.createVector(filename='/vsimem/tmp.gpkg')
        GEOPACKAGE_DRIVER.delete(ogrVector.filename)
        ogrVector = GEOPACKAGE_DRIVER.createVector(filename='tmp.gpkg')
        del ogrVector
        GEOPACKAGE_DRIVER.delete('tmp.gpkg')
        self.assertFalse(exists('tmp.gpkg'))

    def test_prepareCreation(self):
        MEMORY_DRIVER.prepareCreation(filename=None)
        MEMORY_DRIVER.prepareCreation(filename='will be ignored.bsq')
        GEOPACKAGE_DRIVER.prepareCreation(filename='/vsimem/tmp.gpkg')
        GEOPACKAGE_DRIVER.prepareCreation(filename='tmp.gpkg')
