# from __future__ import annotations
from collections import OrderedDict

from dataclasses import dataclass
from typing import Tuple, Union, Dict, Optional

import numpy as np
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.table import Table


@dataclass(frozen=True)
class RasterCollection(object):
    """Raster collection."""
    name: str = ''
    rasters: Tuple[Raster, ...] = tuple()

    def __post_init__(self):
        assert isinstance(self.name, str)
        assert isinstance(self.rasters, tuple)
        for raster in self.rasters:
            assert isinstance(raster, Raster)

    def toBands(self, grid: Grid = None) -> 'Raster':
        """Return raster containing all bands from all raster. If grid is not given, grid from first raster is used."""
        if grid is None:
            assert len(self.rasters) > 0
            grid = self.rasters[0].grid
        bands = list()
        for raster in self.rasters:
            bands.extend(raster.bands)
        return Raster(name='stack', bands=tuple(bands), grid=grid)

    def withName(self, name: str) -> 'RasterCollection':
        return RasterCollection(name=name, rasters=self.rasters)

    def readAsSample(self, grid: Grid = None, **kwargs) -> Tuple[Dict[str, Table], Optional[Table]]:
        """Like Raster.readAsSample(grid, **kwargs), but fields are grouped by raster names."""
        sample, location = self.toBands(grid=grid).readAsSample(grid=grid, **kwargs)
        # split features band-wise
        offset = 0
        samples = OrderedDict()
        for raster in self.rasters:
            names = list(sample.recarray.dtype.names[offset:offset + len(raster.bands)])
            samples[raster.name] = Table(recarray=sample[names])
            offset += len(raster.bands)
        return samples, location

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
