# from __future__ import annotations
from enum import IntEnum
from os import makedirs
from os.path import basename, abspath, dirname

from dataclasses import dataclass
from typing import Tuple, Sequence, Union, Iterator, Optional, List

import numpy as np
from osgeo import gdal

from _classic.hubdsm.core.band import Band
from _classic.hubdsm.core.gdaldriver import VRT_DRIVER
from _classic.hubdsm.core.mask import Mask
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.table import Table


@dataclass(frozen=True)
class Raster(object):
    """Raster."""
    name: str
    bands: Tuple[Band, ...]
    grid: Grid

    def __post_init__(self):
        assert isinstance(self.name, str)
        assert isinstance(self.bands, tuple)
        assert len(self.bands) > 0
        assert isinstance(self.grid, Grid)
        for band in self.bands:
            assert isinstance(band, Band)
        assert isinstance(self.grid, Grid)
        # assert len(self.bandNames) == len(set(self.bandNames)), 'each band name must be unique'

    def __getitem__(self, item):
        if isinstance(item, (list, tuple)):
            selectors = [v + 1 for v in item]
        else:
            numbers = list(range(1, len(self.bands) + 1))
            selectors = numbers[item]
            if not isinstance(selectors, list):
                selectors = [selectors]
        return self.select(selectors=selectors)

    @classmethod
    def open(cls, filenameOrGdalRaster: Union[str, GdalRaster]) -> 'Raster':
        if isinstance(filenameOrGdalRaster, str):
            gdalRaster = GdalRaster.open(filenameOrGdalRaster)
        elif isinstance(filenameOrGdalRaster, GdalRaster):
            gdalRaster = filenameOrGdalRaster
        else:
            raise ValueError('filenameOrGdalRaster')
        return cls.fromGdalRaster(gdalRaster=gdalRaster)

    @staticmethod
    def fromGdalRaster(gdalRaster: GdalRaster) -> 'Raster':
        bands = tuple(Band.fromGdalBand(gdalBand=gdalBand) for gdalBand in gdalRaster.bands)
        return Raster(name=basename(gdalRaster.filename), bands=bands, grid=gdalRaster.grid)

    @staticmethod
    def stack(rasters: Sequence['Raster'], grid: Grid = None) -> 'Raster':
        """Return raster containing all bands from all raster. If grid is not given, grid from first raster is used."""
        if grid is None:
            assert len(rasters) > 0
            grid = rasters[0].grid
        bands = list()
        for raster in rasters:
            bands.extend(raster.bands)
        return Raster(name='stack', bands=tuple(bands), grid=grid)

    @staticmethod
    def create(grid: Grid, bands=1, gdt: int = None, filename: str = None, gco: List[str] = None) -> 'Raster':
        gdalRaster = GdalRaster.create(grid=grid, bands=bands, gdt=gdt, filename=filename, gco=gco)
        return Raster.open(gdalRaster)

    @staticmethod
    def createFromArray(
            array: np.ndarray, grid: Optional[Grid] = None, filename: str = None, gco: List[str] = None
    ) -> 'Raster':
        gdalRaster = GdalRaster.createFromArray(array=array, grid=grid, filename=filename, gco=gco)
        return Raster.open(gdalRaster)

    @property
    def bandNames(self) -> Tuple[str, ...]:
        return tuple(band.name for band in self.bands)

    def band(self, number: int) -> Band:
        return self.bands[number - 1]

    def select(self, selectors: Sequence[Union[str, int]], newBandNames: Sequence[str] = None) -> 'Raster':

        # derives band numbers and new names
        numbers = list()
        bandNames = self.bandNames
        assert isinstance(selectors, (list, tuple))
        for selector in selectors:
            if isinstance(selector, int):
                assert 1 <= selector <= len(self.bands)
                number = selector
            elif isinstance(selector, str):
                number = bandNames.index(selector) + 1
            else:
                raise ValueError(f'unexpected selector "{selector}"')
            numbers.append(number)
        if newBandNames is None:
            newBandNames = (self.bands[number - 1].name for number in numbers)
        else:
            assert len(selectors) == len(newBandNames)

        # subset bands
        bands = tuple(self.bands[number - 1].rename(name) for number, name in zip(numbers, newBandNames))
        raster = Raster(name=self.name, bands=bands, grid=self.grid)
        return raster

    def rename(self, bandNames: Sequence[str] = None) -> 'Raster':
        """Rename bands."""
        if bandNames is None:
            bandNames = self.bandNames
        assert len(bandNames) == len(self.bands)
        selectors = list(range(1, len(self.bands) + 1))
        raster = self.select(selectors=selectors, newBandNames=bandNames)
        return raster

    def addBands(self, raster: 'Raster') -> 'Raster':
        """Return raster containing all bands copied from the first raster and bands from the second input."""
        assert isinstance(raster, Raster)
        return Raster(name=self.name, bands=self.bands + raster.bands, grid=self.grid)

    def withMask(self, mask: Optional['Raster'], invert=False) -> 'Raster':
        """Return raster with new mask raster."""
        if mask is None:
            bands = tuple(band.withMask(mask=None) for band in self.bands)
        else:
            if len(self.bands) == len(mask.bands):
                maskBands = mask.bands
            elif len(mask.bands) == 1:
                maskBands = mask.bands * len(self.bands)
            else:
                raise ValueError(f'expected raster with 1 or {len(self.bands)} bands')
            bands = tuple(
                band.withMask(mask=Mask(band=maskBand, invert=invert)) for band, maskBand in zip(self.bands, maskBands)
            )
        return Raster(name=self.name, bands=bands, grid=self.grid)

    def withName(self, name: str) -> 'Raster':
        return Raster(name=name, bands=self.bands, grid=self.grid)

    def withGrid(self, grid: Grid) -> 'Raster':
        return Raster(name=self.name, bands=self.bands, grid=grid)

    def readAsArray(self, grid: Grid = None, gra: int = None) -> np.ndarray:
        '''Return 3d array.'''
        return np.array(list(self.iterArrays(grid=grid, gra=gra)))

    def readAsMaskArray(self, grid: Grid = None, gra: int = None) -> np.ndarray:
        '''Return 3d mask array.'''
        return np.array(list(self.iterMaskArrays(grid=grid, gra=gra)))

    def iterArrays(self, grid: Grid = None, gra: int = None) -> Iterator[np.ndarray]:
        '''Iterates over 2d band arrays.'''
        if grid is None:
            grid = self.grid
        for band in self.bands:
            yield band.readAsArray(grid=grid, gra=gra)

    def iterMaskArrays(self, grid: Grid = None, gra: int = None) -> Iterator[np.ndarray]:
        '''Iterates over 2d mask band arrays.'''
        if grid is None:
            grid = self.grid
        for band in self.bands:
            array = band.readAsMaskArray(grid=grid, gra=gra)
            if not np.all(np.equal(array.shape, grid.shape)):
                assert 0
            yield array

    class SampleMode(IntEnum):
        strict = 0
        relaxed = 1

    class SampleFieldNames(IntEnum):
        bandNames = 0
        bandIndices = 1

    def readAsSample(
            self, grid: Grid = None, mode: int = None, fieldNames: int = None,
            graRaster: int = None, graMask: int = None,
            xPixel: str = None, yPixel: str = None, xMap: str = None, yMap: str = None,
    ) -> Tuple[Table, Optional[Table]]:
        '''
        Sample raster at masked locations and return tabulated data and (optional) locations.
        Use band names (fieldNames=0 is default) or band indices (fieldNames=1) as field names.
        Use strict sampling (mode=0 is default) to only sample profiles without any missing values
        (useful for fitting maschine learner).
        Use relaxed sampling (mode=1) to also sample profiles with some missing values
        (useful for timeseries analysis).
        Use x/yPixel keywords to name and include sampled pixel locations.
        Use x/yMap keywords to name and include sampled map locations.
        '''
        if grid is None:
            grid = self.grid
        if mode is None:
            mode = self.SampleMode.strict
        if fieldNames is None:
            fieldNames = self.SampleFieldNames.bandNames

        if mode is self.SampleMode.strict:
            maskArray = np.full(shape=grid.shape, fill_value=True, dtype=bool)
            for ma in self.iterMaskArrays(grid=grid, gra=graMask):
                maskArray = np.logical_and(maskArray, ma)
        elif mode is self.SampleMode.relaxed:
            maskArray = np.full(shape=grid.shape, fill_value=False, dtype=bool)
            for ma in self.iterMaskArrays(grid=grid, gra=graMask):
                maskArray = np.logical_or(maskArray, ma)
        else:
            raise ValueError(mode)

        # prepare data table
        arrays = []
        names = []
        for number in range(1, len(self.bands) + 1):
            unmaskedSingleBandRaster = self.select(selectors=[number]).withMask(mask=None)
            array = unmaskedSingleBandRaster.band(number=1).readAsArray(grid=grid, gra=graRaster)
            if fieldNames is self.SampleFieldNames.bandNames:
                name = self.band(number=number).name
            elif fieldNames is self.SampleFieldNames.bandIndices:
                name = str(number - 1)
            else:
                raise ValueError(fieldNames)
            arrays.append(array[maskArray])
            names.append(name)
        dtype = np.dtype(dict(names=names, formats=tuple(array.dtype for array in arrays)))
        sample = np.zeros(len(arrays[0]), dtype=dtype)
        for name, array in zip(names, arrays):
            sample[name] = array
        sample = Table(recarray=np.rec.array(sample))

        # prepare location table
        arrays = []
        names = []
        if xPixel is not None:
            arrays.append(grid.xPixelCoordinatesArray(grid=self.grid)[maskArray])
            names.append(xPixel)
        if yPixel is not None:
            arrays.append(grid.yPixelCoordinatesArray(grid=self.grid)[maskArray])
            names.append(yPixel)
        if xMap is not None:
            arrays.append(grid.xMapCoordinatesArray()[maskArray])
            names.append(xMap)
        if yMap is not None:
            arrays.append(grid.yMapCoordinatesArray()[maskArray])
            names.append(yMap)
        if len(arrays) > 0:
            dtype = np.dtype(dict(names=names, formats=tuple(array.dtype for array in arrays)))
            location = np.zeros(len(arrays[0]), dtype=dtype)
            for name, array in zip(names, arrays):
                location[name] = array
            location = Table(recarray=np.rec.array(location))
        else:
            location = None

        return sample, location

    @property
    def categories(self):
        return self.band(1).gdalBand.categories

    @property
    def setCategories(self):
        return self.band(1).gdalBand.setCategories

    def setNoDataValue(self, value: Union[int, float]):
        for band in self.bands:
            band.setNoDataValue(value=value)

    @property
    def rasterize(self):
        return self.band(1).rasterize

    def fill(self, value: Union[int, float]):
        for band in self.bands:
            band.fill(value=value)

    def saveAsVrt(self, filename: str, gra=gdal.GRA_NearestNeighbour) -> 'Raster':

        # create VRT
        # - create stack with first band of each raster
        tmpfilename = '/vsimem/hubdsm.core.raster.Raster.saveAsVrt/tmp.vrt'
        VRT_DRIVER.prepareCreation(filename=tmpfilename)
        minX, minY = self.grid.extent.ll
        maxX, maxY = self.grid.extent.ur
        outputBounds = minX, minY, maxX, maxY
        xRes, yRes = self.grid.resolution
        options = gdal.BuildVRTOptions(
            separate=True, outputBounds=outputBounds, xRes=xRes, yRes=yRes, bandList=[1], resampleAlg=gra
        )
        filenames = [abspath(band.filename) for band in self.bands]
        gdal.BuildVRT(destName=tmpfilename, srcDSOrSrcDSTab=filenames, options=options)
        file = gdal.VSIFOpenL(tmpfilename, 'r')
        lines = [line + '\n' for line in gdal.VSIFReadL(1, 100000, file).decode().split('\n')]
        gdal.VSIFCloseL(file)
        gdal.Unlink(tmpfilename)

        # - write sources
        try:
            makedirs(dirname(filename))
        except:
            pass
        with open(filename, 'w') as file:
            bandIndex = 0
            for line in lines:
                if line.endswith('</SourceBand>\n'):
                    file.write(f'      <SourceBand>{self.bands[bandIndex].number}</SourceBand>\n', )
                    bandIndex += 1
                else:
                    file.write(line)
        # - set metadata
        gdalRaster = GdalRaster.open(filename)
        gdalRaster.band(1).setCategories(self.categories)
        for gdalBand, band in zip(gdalRaster.bands, self.bands):
            gdalBand.setNoDataValue(band.noDataValue)
            gdalBand.setDescription(band.name)

        # it seams that flushing the cache is not sufficient, so we re-open the vrt
        del gdalRaster

        raster = Raster.open(filename)
        return raster

    def flushCache(self):
        for band in self.bands:
            band.flushCache()
