# from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, Any, List, Dict

import numpy as np
from osgeo import gdal
from osgeo.gdal import GDALRasterizeOptions

from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.gdalmetadatavalueformatter import GdalMetadataValueFormatter
from _classic.hubdsm.core.error import ProjectionMismatchError
from _classic.hubdsm.core.ogrlayer import OgrLayer


@dataclass(frozen=True)
class GdalBand(object):
    """Raster band dataset."""
    gdalDataset: gdal.Dataset
    gdalBand: gdal.Band
    number: int

    def __post_init__(self):
        assert isinstance(self.gdalDataset, gdal.Dataset)
        assert isinstance(self.gdalBand, gdal.Band)
        assert isinstance(self.number, int)

    @staticmethod
    def open(filenameOrGdalRaster: Union[str, 'GdalRaster'], number: int, access: int = gdal.GA_ReadOnly) -> 'GdalBand':
        from _classic.hubdsm.core.gdalraster import GdalRaster
        if isinstance(filenameOrGdalRaster, str):
            gdalRaster = GdalRaster.open(filenameOrGdalRaster, access=access)
        else:
            gdalRaster = filenameOrGdalRaster
        assert isinstance(gdalRaster, GdalRaster)
        return gdalRaster.band(number=number)

    @property
    def index(self):
        """Return band index."""
        return self.number - 1

    @property
    def raster(self) -> 'GdalRaster':
        """Return raster dataset."""
        from _classic.hubdsm.core.gdalraster import GdalRaster
        return GdalRaster(gdalDataset=self.gdalDataset)

    @property
    def gdalDataType(self) -> int:
        """Return GDAL data type."""
        return self.gdalBand.DataType

    @property
    def grid(self) -> Grid:
        """Return grid."""
        return self.raster.grid

    def flushCache(self):
        self.gdalDataset.FlushCache()
        self.gdalBand.FlushCache()

    def readAsArray(self, grid: Grid = None, gra: int = None) -> np.ndarray:
        """Return 2d array."""

        if gra is None:
            gra = gdal.GRA_NearestNeighbour

        if grid is None:
            grid = self.grid
            array = self.gdalBand.ReadAsArray(resample_alg=gra)
        else:
            assert isinstance(grid, Grid)
            if grid.projection != self.grid.projection:
                raise ProjectionMismatchError()
            if grid.extent.within(self.grid.extent):
                # read data directly
                resolution = self.grid.resolution
                extent = self.grid.extent
                buf_ysize, buf_xsize = grid.shape
                xoff = round((grid.extent.xmin - extent.xmin) / resolution.x, 0)
                yoff = round((extent.ymax - grid.extent.ymax) / resolution.y, 0)
                xsize = round((grid.extent.xmax - grid.extent.xmin) / resolution.x, 0)
                ysize = round((grid.extent.ymax - grid.extent.ymin) / resolution.y, 0)
                array = self.gdalBand.ReadAsArray(
                    xoff=xoff, yoff=yoff, win_xsize=xsize, win_ysize=ysize,
                    buf_xsize=buf_xsize, buf_ysize=buf_ysize,
                    resample_alg=gra
                )
            else:
                # translate into target grid and read
                ul = grid.extent.ul
                lr = grid.extent.lr
                xRes, yRes = grid.resolution.x, grid.resolution.y
                _translateOptions = gdal.TranslateOptions(
                    format='MEM', resampleAlg=gra, projWin=[ul.x, ul.y, lr.x, lr.y], xRes=xRes, yRes=yRes,
                    bandList=[self.number]
                )
                translateOptions = gdal.TranslateOptions(
                    format='MEM', resampleAlg=gra, width=grid.shape.x, height=grid.shape.y,
                    projWin=[ul.x, ul.y, lr.x, lr.y],
                    bandList=[self.number]
                )

                ds: gdal.Dataset = gdal.Translate(destName='', srcDS=self.gdalDataset, options=translateOptions)
                array = ds.GetRasterBand(1).ReadAsArray()

        assert isinstance(array, np.ndarray)
        assert array.ndim == 2

        if not np.all(np.equal(array.shape, grid.shape)):
            assert 0

        return array

    def writeArray(self, array: np.ndarray, grid: Optional[Grid] = None):
        """Write raster data."""

        assert isinstance(array, np.ndarray), array
        assert array.ndim == 2, array.ndim
        if grid is None:
            grid = self.grid
        assert isinstance(grid, Grid), grid
        assert array.shape == tuple(grid.shape), (array.shape, grid.shape)
        assert self.raster.grid.projection == grid.projection

        xoff = int(round((grid.extent.xmin - self.grid.extent.xmin) / self.grid.resolution.x, 0))
        yoff = int(round((self.grid.extent.ymax - grid.extent.ymax) / self.grid.resolution.y, 0))

        self.gdalBand.WriteArray(array, xoff=xoff, yoff=yoff)

    def fill(self, value):
        """Write constant ``value`` to the whole raster band."""
        self.gdalBand.Fill(value)

    def rasterize(
            self, layer: Union[OgrLayer, str], burnValue: Union[int, float] = 1, burnAttribute: str=None, allTouched=False,
            filterSQL: str = None
    ):
        '''Burn layer into band.'''
        if isinstance(layer, OgrLayer):
            ogrLayer = layer
        elif isinstance(layer, str):
            ogrLayer = OgrLayer.open(layer)
        else:
            raise ValueError(layer)

        assert isinstance(ogrLayer, OgrLayer)
        if ogrLayer.projection != self.grid.projection:
            raise ProjectionMismatchError()
        rasterizeLayerOptions = list()
        if allTouched:
            rasterizeLayerOptions.append('ALL_TOUCHED=TRUE')
        if burnAttribute:
            rasterizeLayerOptions.append('ATTRIBUTE=' + burnAttribute)
        gdal.RasterizeLayer(
            self.gdalDataset, [1], ogrLayer.ogrLayer, burn_values=[burnValue], options=rasterizeLayerOptions
        )

    def setMetadataItem(self, key, value: Union[Any, List[Any]], domain=''):
        """Set metadata item."""
        if value is None:
            return
        key = key.replace(' ', '_')
        gdalString = GdalMetadataValueFormatter.valueToString(value)
        self.gdalBand.SetMetadataItem(key, gdalString, domain)

    def setMetadataDomain(self, values: Dict[str, Union[Any, List[Any]]], domain: str):
        """Set the metadata domain."""
        assert isinstance(values, dict)
        for key, value in values.items():
            self.setMetadataItem(key=key, value=value, domain=domain)

    def setMetadataDict(self, metadataDict=Dict[str, Dict[str, Union[Any, List[Any]]]]):
        """Set the metadata."""
        assert isinstance(metadataDict, dict)
        for domain, metadataDomain in metadataDict.items():
            self.setMetadataDomain(values=metadataDomain, domain=domain)

    def metadataItem(self, key, domain='', dtype=None, default=None):
        """Return the metadata item."""
        key = key.replace(' ', '_')
        gdalString = self.gdalBand.GetMetadataItem(key, domain)
        if gdalString is not None:
            value = GdalMetadataValueFormatter.stringToValue(gdalString, dtype=dtype)
        else:
            value = default
        return value

    def metadataDomain(self, domain=''):
        """Return the metadata dictionary for the given ``domain``."""
        metadataDomain = dict()
        for key in self.gdalBand.GetMetadata(domain):
            key = key.replace('_', ' ')
            metadataDomain[key] = self.metadataItem(key=key, domain=domain)
        return metadataDomain

    @property
    def metadataDict(self):
        """Return the metadata dictionary for all domains."""
        metadataDict = dict()
        for domain in self.metadataDomainList:
            metadataDict[domain] = self.metadataDomain(domain=domain)
        return metadataDict

    def setNoDataValue(self, value):
        """Set no data value."""
        if value is not None:
            self.gdalBand.SetNoDataValue(float(value))

    @property
    def noDataValue(self) -> Optional[float]:
        """Return no data value."""
        return self.gdalBand.GetNoDataValue()

    def setDescription(self, value):
        """Set description."""
        self.gdalBand.SetDescription(value)

    @property
    def description(self) -> str:
        """Return description."""
        return self.gdalBand.GetDescription()

    def setCategories(self, categories: Optional[List[Category]]):
        """Set categories."""
        if categories is not None:
            ids = [int(c.id) for c in categories]
            maxId = int(max(ids))
            names = ['n/a'] * (maxId + 1)
            colors = [Color(red=0, green=0, blue=0)] * (maxId + 1)
            for c in categories:
                names[int(c.id)] = c.name
                colors[int(c.id)] = c.color
            self._setCategoryNames(names=names)
            self._setCategoryColors(colors)

    def _setCategoryNames(self, names: List[str]):
        """Set category names."""
        self.gdalBand.SetCategoryNames(names)

    def _setCategoryColors(self, colors: List[Color]):
        """Set category colors."""
        colorTable = gdal.ColorTable()
        for i, color in enumerate(colors):
            assert isinstance(color, Color)
            colorTable.SetColorEntry(i, tuple(color))
        self.gdalBand.SetColorTable(colorTable)

    @property
    def categories(self) -> Optional[List[Category]]:
        """Return categories."""
        categories = list()
        for id, (name, color) in enumerate(zip(self._categoryNames(), self._categoryColors())):
            if name == 'n/a' and color == Color():
                continue
            categories.append(Category(id=id, name=name, color=color))
        if len(categories) == 0:
            categories = None
        return categories

    def _categoryNames(self) -> List[str]:
        """Return category names."""
        names = self.gdalBand.GetCategoryNames()
        if names is None:
            return list()
        return names

    def _categoryColors(self) -> List[Color]:
        """Return category colors."""
        colorTable = self.gdalBand.GetColorTable()
        colors = list()
        if colorTable is not None:
            for i in range(colorTable.GetCount()):
                rgba = colorTable.GetColorEntry(i)
                colors.append(Color(*rgba))
        return colors

    @property
    def metadataDomainList(self):
        """Returns the list of metadata domain names."""
        domains = self.gdalBand.GetMetadataDomainList()
        return domains if domains is not None else []

    @property
    def wavelength(self) -> Optional[float]:
        """Return center wavelength in nanometers."""
        wavelength = self.metadataItem(key='wavelength', domain='ENMAPBOX', dtype=float)
        if wavelength is None:
            enviWavelengths = self.raster.metadataItem(key='wavelength', domain='ENVI', dtype=float)
            if enviWavelengths is None:
                return None
            enviWavelength = enviWavelengths[self.number - 1]
            unit = self.raster.metadataItem(key='wavelength units', domain='ENVI')
            if unit in ['Micrometers', 'micrometers', 'um']:
                wavelength = enviWavelength * 1000.
            else:
                wavelength = enviWavelength
        return wavelength

    def setWavelength(self, value: float):
        """Set center wavelength in nanometers."""
        assert isinstance(value, float)
        self.setMetadataItem(key='wavelength', value=value, domain='ENMAPBOX')

    @property
    def fwhm(self) -> Optional[float]:
        """Return full width at half maximum in nanometers."""
        fwhm = self.metadataItem(key='fwhm', domain='ENMAPBOX', dtype=float)
        if fwhm is None:
            enviFwhm = self.raster.metadataItem(key='fwhm', domain='ENVI', dtype=float)
            if enviFwhm is None:
                return None
            enviFwhm = enviFwhm[self.number - 1]
            unit = self.raster.metadataItem(key='wavelength units', domain='ENVI')
            if unit in ['Micrometers', 'micrometers', 'um']:
                fwhm = enviFwhm * 1000.
            else:
                fwhm = enviFwhm
        return fwhm

    def setFwhm(self, value: float):
        """Set full width at half maximum in nanometers."""
        assert isinstance(value, float)
        self.setMetadataItem(key='fwhm', value=value, domain='ENMAPBOX')

    @property
    def isBadBand(self) -> bool:
        """Return wether band is bad."""
        isBadBand = self.metadataItem(key='bad band', domain='ENMAPBOX', dtype=int)
        if isBadBand is None:
            enviBbl = self.raster.metadataItem(key='bbl', domain='ENVI', dtype=int)
            if enviBbl is None:
                return False
            isBadBand = enviBbl[self.number - 1] == 0
        else:
            isBadBand = isBadBand == 1
        return isBadBand

    def setIsBadBand(self, value):
        """Set wether band is bad."""
        assert isinstance(value, bool)
        self.setMetadataItem(key='bad band', value=int(value), domain='ENMAPBOX')

    def translate(
            self, grid: Grid = None, filename: str = None, driver: 'GdalDriver' = None, gco: List[str] = None,
            gra: int = None, **kwargs
    ) -> 'GdalBand':
        '''Return translated raster band.'''
        return self.raster.translate(
            grid=grid, filename=filename, driver=driver, gco=gco, gra=gra, bandList=[self.number], **kwargs
        ).band(1)
