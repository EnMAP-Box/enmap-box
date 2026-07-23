# from __future__ import annotations
from dataclasses import dataclass, field
from os import makedirs
from os.path import splitext, isabs, abspath, exists, dirname
from typing import List, Optional, Type

import numpy as np
from osgeo import gdal, gdal_array
from osgeo.gdal_array import NumericTypeCodeToGDALTypeCode

from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.shape import RasterShape


@dataclass
class GdalDriver(object):
    name: str
    options: List[str] = field(default_factory=list)

    def __post_init__(self):
        assert self.gdalDriver is not None
        assert isinstance(self.options, list)

    @classmethod
    def fromFilename(cls, filename: Optional[str]) -> 'GdalDriver':

        if filename is None or filename == '':
            return MEM_DRIVER

        ext = splitext(filename)[1][1:].lower()
        if ext in ['bsq', 'sli', 'esl']:
            return ENVI_BSQ_DRIVER
        if ext == 'bil':
            return ENVI_BIL_DRIVER
        if ext == 'bip':
            return ENVI_BIP_DRIVER
        if ext in ['tif', 'tiff']:
            return GTIFF_DRIVER
        if ext == 'img':
            return ERDAS_DRIVER
        if ext == 'vrt':
            return VRT_DRIVER
        return ENVI_BSQ_DRIVER

    @property
    def gdalDriver(self) -> gdal.Driver:
        """Returns the GDAL driver object."""
        gdalDriver = gdal.GetDriverByName(self.name)
        assert gdalDriver is not None
        return gdalDriver

    def createRaster(
            self, grid: Grid, bands=1, gdt: int = gdal.GDT_Float32, filename: str = None, gco: List[str] = None
    ) -> GdalRaster:
        """Create new GDAL raster."""

        assert isinstance(grid, Grid)
        assert isinstance(bands, int) and bands >= 0
        filename = self.prepareCreation(filename)
        if gco is None:
            gco = self.options
        assert isinstance(gco, list)
        utf8_path = filename
        ysize, xsize = grid.shape
        gdalDataset = self.gdalDriver.Create(utf8_path, xsize, ysize, bands, gdt, gco)
        gdalDataset.SetProjection(grid.projection.wkt)
        gdalDataset.SetGeoTransform(grid.geoTransform.gdalGeoTransform())
        return GdalRaster(gdalDataset=gdalDataset)

    def createFromArray(
            self, array: np.ndarray, grid: Optional[Grid] = None, filename: str = None, gco: List[str] = None
    ) -> GdalRaster:
        """Create new GDAL raster from array."""
        assert isinstance(array, np.ndarray)
        assert array.ndim == 3
        gdt = NumericTypeCodeToGDALTypeCode(array.dtype)
        shape = RasterShape(*array.shape)
        gdalRaster = self.createFromShape(shape=shape, gdt=gdt, grid=grid, filename=filename, gco=gco)
        gdalRaster.writeArray(array=array, grid=grid)
        return gdalRaster

    def createFromShape(
            self, shape: RasterShape, gdt: int = None, grid: Grid = None, filename: str = None,
            gco: List[str] = None
    ) -> GdalRaster:
        """Create new GDAL raster from array shape."""
        assert isinstance(shape, RasterShape)
        if grid is None:
            grid = Grid.makePseudoGridFromShape(shape=shape.gridShape)
        if gdt is None:
            gdt = gdal.GDT_Float32
        gdalRaster = self.createRaster(grid=grid, bands=shape.z, gdt=gdt, filename=filename, gco=gco)
        return gdalRaster

    def delete(self, filename: str):
        """Delete GDAL raster file on disk or unlink on /vsimem/."""
        if filename.startswith('/vsimem/'):
            try:
                gdal.Unlink(filename)
            except:
                pass
        if exists(filename):
            try:
                self.gdalDriver.Delete(filename)
            except:
                pass

    def prepareCreation(self, filename: str) -> str:
        """Return absolute filename and create root folder/subfolders if not existing."""

        if filename is None or filename == '':
            return ''

        if self == MEM_DRIVER:
            return ''

        assert isinstance(filename, str)
        if filename.startswith('/vsimem/'):
            self.delete(filename)
            return filename

        if not isabs(filename):
            filename = abspath(filename)
        if not exists(dirname(filename)):
            makedirs(dirname(filename))
        self.delete(filename=filename)
        return filename


MEM_DRIVER = GdalDriver(name='MEM')
VRT_DRIVER = GdalDriver(name='VRT')
ENVI_DRIVER = GdalDriver(name='ENVI')
ENVI_BSQ_DRIVER = GdalDriver(name='ENVI', options=['INTERLEAVE=BSQ'])
ENVI_BIL_DRIVER = GdalDriver(name='ENVI', options=['INTERLEAVE=BIL'])
ENVI_BIP_DRIVER = GdalDriver(name='ENVI', options=['INTERLEAVE=BIP'])
GTIFF_DRIVER = GdalDriver(name='GTiff', options=['INTERLEAVE=BAND'])
ERDAS_DRIVER = GdalDriver(name='HFA')
