# from __future__ import annotations
from dataclasses import dataclass, field
from os import makedirs
from os.path import splitext, isabs, abspath, exists, dirname
from typing import List, Optional

import numpy as np
from osgeo import gdal, gdal_array, ogr
from osgeo.gdal_array import NumericTypeCodeToGDALTypeCode

from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.ogrvector import OgrVector
from _classic.hubdsm.core.projection import Projection
from _classic.hubdsm.core.shape import RasterShape


@dataclass
class OgrDriver(object):
    name: str

    def __post_init__(self):
        assert self.ogrDriver is not None

    @classmethod
    def fromFilename(cls, filename: Optional[str]) -> 'OgrDriver':
        """Derive driver from file extension."""
        if filename is None or filename == '':
            return MEMORY_DRIVER
        ext = splitext(filename)[1][1:].lower()
        if ext == 'shp':
            return SHAPEFILE_DRIVER
        if ext == 'gpkg':
            return GEOPACKAGE_DRIVER
        raise ValueError(f'unknown vector file extention: {ext}')

    @property
    def ogrDriver(self) -> ogr.Driver:
        """Return the OGR driver object."""
        ogrDriver = ogr.GetDriverByName(self.name)
        return ogrDriver

    def createVector(self, filename: str = None) -> OgrVector:
        """Create new OGR vector."""
        filename = self.prepareCreation(filename=filename)
        ds = self.ogrDriver.CreateDataSource(filename)
        return OgrVector(ogrDataSource=ds)

    def delete(self, filename: str):
        """Delete OGR data source."""

        try:
            if filename.lower().startswith('/vsimem/'):
                gdal.Unlink(filename)
            else:
                self.ogrDriver.DeleteDataSource(filename)
        except:
            pass

    def prepareCreation(self, filename: str) -> str:
        """Return absolute filename and create root folder/subfolders if not existing."""

        if filename is None or filename == '':
            return ''

        if self == MEMORY_DRIVER:
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


MEMORY_DRIVER = OgrDriver(name='MEMORY')
SHAPEFILE_DRIVER = OgrDriver(name='ESRI Shapefile')
GEOPACKAGE_DRIVER = OgrDriver(name='GPKG')
