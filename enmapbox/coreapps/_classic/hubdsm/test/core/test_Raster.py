from unittest.case import TestCase

import numpy as np
from osgeo import gdal
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from enmapbox.exampledata import enmap, hires
from _classic.hubdsm.core.band import Band
from _classic.hubdsm.core.error import ProjectionMismatchError
from _classic.hubdsm.core.extent import Extent
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.mask import Mask
from _classic.hubdsm.core.pixellocation import PixelLocation
from _classic.hubdsm.core.projection import Projection, WGS84_PROJECTION
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.resolution import Resolution
from _classic.hubdsm.core.shape import GridShape
from _classic.hubdsm.core.size import Size


class TestRaster(TestCase):

    def test_open(self):
        try:
            Raster.open(None)
        except ValueError:
            pass

    def test_fromGdalRaster(self):
        gdalRaster = GdalRaster.open(enmap)
        raster = Raster.fromGdalRaster(gdalRaster=gdalRaster)
        for number, band in enumerate(raster.bands, 1):
            self.assertEqual(band.number, number)
            self.assertEqual(band.filename, enmap)

    def test_readMultiResolution(self):
        array1 = np.array(range(2 ** 2), dtype=np.float32).reshape((1, 2, 2))
        array2 = np.array(range(4 ** 2), dtype=np.float32).reshape((1, 4, 4))
        grid1 = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=4, y=4)), resolution=Resolution(x=2, y=2),
            projection=WGS84_PROJECTION
        )
        grid2 = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=4, y=4)), resolution=Resolution(x=1, y=1),
            projection=WGS84_PROJECTION
        )

        raster1 = Raster.open(MEM_DRIVER.createFromArray(array=array1, grid=grid1)).rename(bandNames=['B1'])
        raster2 = Raster.open(MEM_DRIVER.createFromArray(array=array2, grid=grid2)).rename(bandNames=['B2'])
        raster = raster1.addBands(raster=raster2)
        assert raster.grid.equal(grid1)
        assert np.all(raster1.readAsArray() == array1)
        assert np.all(raster2.readAsArray() == array2)
        gold = [[[0., 1.], [2., 3.]], [[2.5, 4.5], [10.5, 12.5]]]
        lead = raster.readAsArray(gra=gdal.GRA_Average)
        assert np.all(np.equal(lead, gold))

    def test_readBlockwise(self):
        array = np.array(range(5 * 4)).reshape((1, 5, 4))
        raster = Raster.fromGdalRaster(MEM_DRIVER.createFromArray(array=array))
        leads = list()
        for subgrid in raster.grid.subgrids(shape=GridShape(y=2, x=2)):
            leads.append(raster.readAsArray(grid=subgrid)[0])
        golds = [
            [[0, 1], [4, 5]],
            [[2, 3], [6, 7]],
            [[8, 9], [12, 13]],
            [[10, 11], [14, 15]],
            [[16, 17]]
        ]
        for gold, lead in zip(golds, leads):
            assert np.all(np.equal(gold, lead))

    def test_readOutsideExtent(self):
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=2, y=2)),
            resolution=Resolution(x=1, y=1),
            projection=WGS84_PROJECTION
        )
        grid2 = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=4, y=4)),
            resolution=Resolution(x=1, y=1),
            projection=WGS84_PROJECTION
        )

        raster1 = Raster.createFromArray(array=np.ones(shape=(1, 2, 2)), grid=grid)
        print(raster1.readAsArray(grid=grid2))

    def test_readWithInvalidProjection(self):
        raster = Raster.open(enmap)
        grid = Grid(
            extent=Extent(ul=Location(x=0, y=0), size=Size(x=90, y=90)), resolution=raster.grid.resolution,
            projection=WGS84_PROJECTION
        )
        try:
            raster.readAsArray(grid=grid)
        except ProjectionMismatchError:
            pass

    def test_select(self):
        raster = Raster.open(
            MEM_DRIVER.createFromArray(array=np.ones(shape=(3, 10, 10)))
        ).rename(bandNames=['B1', 'B2', 'B3'])
        self.assertEqual(raster.select(selectors=[1, 3]).bandNames, ('B1', 'B3'))
        self.assertEqual(raster.select(selectors=['B1', 'B3']).bandNames, ('B1', 'B3'))
        try:
            raster.select(selectors=[None])
        except ValueError:
            pass

    def test_band(self):
        raster = Raster.open(
            MEM_DRIVER.createFromArray(array=np.ones(shape=(3, 10, 10)))
        ).rename(bandNames=['B1', 'B2', 'B3'])
        self.assertEqual(raster.band(number=2), raster.bands[1])

    def test_rename(self):
        raster = Raster.open(
            MEM_DRIVER.createFromArray(array=np.ones(shape=(3, 10, 10)))
        ).rename(bandNames=['B1', 'B2', 'B3']).withName(name='Raster')
        self.assertEqual(raster.rename().bandNames, ('B1', 'B2', 'B3'))
        self.assertEqual(raster.rename().name, 'Raster')
        self.assertEqual(raster.withName('NewRaster').name, 'NewRaster')

    def test_withMask(self):
        raster = Raster.open(
            MEM_DRIVER.createFromArray(array=np.ones(shape=(3, 10, 10)))
        )
        raster = raster.withMask(mask=raster)
        for band in raster.bands:
            self.assertEqual(band.mask.band.number, band.number)
        raster = raster.withMask(mask=raster.select(selectors=[1]))
        for band in raster.bands:
            self.assertEqual(band.mask.band.number, 1)
        try:
            raster.withMask(mask=raster.select(selectors=[1, 2]))
        except ValueError:
            pass

    def test_iterArrays(self):
        mask = Raster.open(MEM_DRIVER.createFromArray(array=np.array([[[1]], [[0]]])))
        raster = Raster.open(MEM_DRIVER.createFromArray(array=np.array([[[10]], [[20]]])))
        raster = raster.withMask(mask=mask)
        self.assertTrue(np.all(np.equal(raster.readAsArray(), [[[10]], [[20]]])))
        self.assertTrue(np.all(np.equal(raster.readAsMaskArray(), [[[True]], [[False]]])))

    def test_readAsSample(self):
        mask = Raster.open(
            MEM_DRIVER.createFromArray(
                array=np.array(
                    [[[1, 1, 1, 1, 0, 0, 0, 0]],
                     [[1, 1, 1, 1, 0, 0, 0, 0]]]
                )
            )
        )
        raster = Raster.open(
            MEM_DRIVER.createFromArray(
                array=np.array(
                    [[[-1, 11, 12, 13, -1, 14, 15, 16]],
                     [[-1, 21, 22, -1, -1, 24, 25, 26]]]
                )
            )
        )
        for band in raster.bands:
            band.gdalBand.setNoDataValue(-1)
        raster = raster.withMask(mask=mask).rename(bandNames=['B1', 'B2'])

        # test field names
        sample, location = raster.readAsSample(fieldNames=Raster.SampleFieldNames.bandNames)
        assert isinstance(sample.B1, np.ndarray)
        assert isinstance(sample.B2, np.ndarray)
        assert isinstance(sample['B1'], np.ndarray)
        assert isinstance(sample['B2'], np.ndarray)
        sample, location = raster.readAsSample(fieldNames=Raster.SampleFieldNames.bandIndices)
        assert isinstance(sample['0'], np.ndarray)
        assert isinstance(sample['1'], np.ndarray)

        # sample also incomplete profiles (e.g. required for timeseries analysis)
        sample, location = raster.readAsSample(xPixel='x', yPixel='y', mode=Raster.SampleMode.relaxed)
        self.assertTrue(np.all(np.equal(location.x, [1, 2, 3])))
        self.assertTrue(np.all(np.equal(location.y, [0, 0, 0])))
        self.assertTrue(np.all(np.equal(sample.B1, [11, 12, 13])))
        self.assertTrue(np.all(np.equal(sample.B2, [21, 22, -1])))

        # sample only complete profiles (e.g. required for classification)
        sample, location = raster.readAsSample(xPixel='x', yPixel='y', mode=Raster.SampleMode.strict)
        self.assertTrue(np.all(np.equal(location.x, [1, 2])))
        self.assertTrue(np.all(np.equal(location.y, [0, 0])))
        self.assertTrue(np.all(np.equal(sample.B1, [11, 12])))
        self.assertTrue(np.all(np.equal(sample.B2, [21, 22])))

        # sample on subgrid
        subgrid = raster.grid.subgrid(offset=PixelLocation(x=2, y=0), shape=GridShape(x=2, y=1))
        sample, location = raster.readAsSample(grid=subgrid, xPixel='x', yPixel='y', mode=Raster.SampleMode.relaxed)
        self.assertTrue(np.all(np.equal(location.x, [2, 3])))
        self.assertTrue(np.all(np.equal(location.y, [0, 0])))
        self.assertTrue(np.all(np.equal(sample.B1, [12, 13])))
        self.assertTrue(np.all(np.equal(sample.B2, [22, -1])))

    def test___getitem__(self):
        raster = Raster.open(MEM_DRIVER.createFromArray(array=np.ones(shape=(3, 5, 5)))).rename(['B1', 'B2', 'B3'])
        self.assertTupleEqual(raster.bandNames, ('B1', 'B2', 'B3'))
        self.assertTupleEqual(raster[1].bandNames, ('B2',))
        self.assertTupleEqual(raster[1:].bandNames, ('B2', 'B3'))
        self.assertTupleEqual(raster[(0, 2)].bandNames, ('B1', 'B3'))

    def test_saveAsVrt(self):
        pass