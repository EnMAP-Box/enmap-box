# from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Union

import numpy as np
from osgeo import gdal

from _classic.hubdsm.core.gdalband import GdalBand
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.mask import Mask
from _classic.hubdsm.core.table import Table


@dataclass
class Band(object):
    """Raster band."""
    name: str
    filename: str
    number: int
    mask: Optional[Mask]
    _gdalBand: Optional[GdalBand]

    def __post_init__(self):
        assert isinstance(self.name, str)
        assert isinstance(self.filename, str)
        assert isinstance(self.number, int) and self.number >= 1
        assert isinstance(self.mask, (Mask, type(None)))
        assert isinstance(self._gdalBand, (GdalBand, type(None)))

    @staticmethod
    def fromGdalBand(gdalBand: GdalBand):
        band = Band(
            name=gdalBand.description, filename=gdalBand.gdalDataset.GetDescription(), number=gdalBand.number,
            mask=None, _gdalBand=gdalBand
        )
        return band

    @property
    def gdalBand(self) -> GdalBand:
        '''Return GdalBand instance.'''
        if self._gdalBand is None:
            self._gdalBand = GdalBand.open(self.filename, number=self.number)
        return self._gdalBand

    def rename(self, name) -> 'Band':
        '''Return band with new name.'''
        return Band(name=name, filename=self.filename, number=self.number, mask=self.mask, _gdalBand=self._gdalBand)

    def withMask(self, mask: Optional[Mask]) -> 'Band':
        '''Return band with mask.'''
        return Band(
            name=self.name, filename=self.filename, number=self.number, mask=mask,
            _gdalBand=self._gdalBand
        )

    def readAsArray(self, grid: Grid = None, gra: int = None) -> np.ndarray:
        '''Return 2d array.'''
        return self.gdalBand.readAsArray(grid=grid, gra=gra)

    def readAsMaskArray(self, grid: Grid = None, gra: int = None) -> np.ndarray:
        '''Return 2d mask array. Combines the internal mask given by the no data value and the external mask.'''
        if grid is None:
            grid = self.gdalBand.grid
        noDataValue = self.gdalBand.noDataValue
        array = self.readAsArray(grid=grid, gra=gra)
        if noDataValue is None:
            maskArray1 = np.full_like(array, fill_value=True, dtype=bool)
        elif np.isnan(noDataValue):
            maskArray1 = np.logical_not(np.isnan(array))
        else:
            maskArray1 = array != noDataValue
        if self.mask is not None:
            maskArray2 = self.mask.readAsArray(grid=grid, gra=gra)
            maskArray = np.logical_and(maskArray1, maskArray2)
        else:
            maskArray = maskArray1

        if not np.all(np.equal(maskArray.shape, grid.shape)):
            assert 0

        return maskArray

    def readAsSample(self, grid: Grid = None, mode: int = None, fieldNames: int = None,
            graRaster: int = None, graMask: int = None,
            xPixel: str = None, yPixel: str = None, xMap: str = None, yMap: str = None,
    ) -> Union[Table, Optional[Table]]:

        from _classic.hubdsm.core.raster import Raster
        if grid is None:
            grid = self.gdalBand.grid

        raster = Raster(name=self.name, bands=(self,), grid=grid)
        return raster.readAsSample(
            grid=grid, mode=mode, fieldNames=fieldNames, graRaster=graRaster, graMask=graMask, xPixel=xPixel,
            yPixel=yPixel, xMap=xMap, yMap=yMap
        )

    @property
    def rasterize(self):
        return self.gdalBand.rasterize

    @property
    def noDataValue(self):
        return self.gdalBand.noDataValue

    @property
    def setNoDataValue(self):
        return self.gdalBand.setNoDataValue

    @property
    def fill(self):
        return self.gdalBand.fill

    @property
    def flushCache(self):
        return self.gdalBand.flushCache

    @property
    def wavelength(self):
        return self.gdalBand.wavelength

    @property
    def fwhm(self):
        return self.gdalBand.fwhm

    @property
    def isBadBand(self):
        return self.gdalBand.isBadBand

    @property
    def metadataDict(self):
        return self.gdalBand.metadataDict

    @property
    def metadataItem(self):
        return self.gdalBand.metadataItem

    @property
    def metadataDomain(self):
        return self.gdalBand.metadataDomain

    @property
    def setMetadataDict(self):
        return self.gdalBand.setMetadataDict

    @property
    def setMetadataItem(self):
        return self.gdalBand.setMetadataItem

    @property
    def setMetadataDomain(self):
        return self.gdalBand.setMetadataDomain
