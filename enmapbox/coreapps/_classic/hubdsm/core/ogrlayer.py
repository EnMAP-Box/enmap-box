# from __future__ import annotations
from typing import List, Iterator, Sequence, Tuple, Union, Callable

from dataclasses import dataclass

from osgeo import ogr, gdal

from _classic.hubdsm.core.extent import Extent
from _classic.hubdsm.core.geometry import Geometry
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.projection import Projection
from _classic.hubdsm.core.size import Size
from _classic.hubdsm.core.typing import Number


@dataclass(frozen=True)
class OgrLayer(object):
    """OGR vector layer dataset."""
    ogrLayer: ogr.Layer
    ogrDataSource: ogr.DataSource

    def __post_init__(self):
        assert isinstance(self.ogrLayer, ogr.Layer)

    @staticmethod
    def open(filename: str, layerNameOrIndex=None) -> 'OgrLayer':
        from _classic.hubdsm.core.ogrvector import OgrVector
        if layerNameOrIndex is None:
            if '|' in filename:
                filename, tmp = filename.split('|')
                _, layerNameOrIndex = tmp.split('=')
        return OgrVector.open(filename=filename).layer(nameOrIndex=layerNameOrIndex)

    @property
    def vector(self) -> 'OgrVector':
        """Return OGR vector."""
        from _classic.hubdsm.core.ogrvector import OgrVector
        return OgrVector(ogrDataSource=self.ogrDataSource)

    @property
    def name(self):
        """Return name."""
        return self.ogrLayer.GetName()

    @property
    def projection(self):
        """Return projection."""
        return Projection(wkt=self.ogrLayer.GetSpatialRef().ExportToWkt())

    @property
    def geometryType(self) -> int:
        """Return OGR WKB geometry type."""
        return self.ogrLayer.GetGeomType()

    @property
    def extent(self):
        """Return layer extent."""
        xmin, xmax, ymin, ymax = self.ogrLayer.GetExtent()
        return Extent(ul=Location(x=xmin, y=ymax), size=Size(x=xmax - xmin, y=ymax - ymin))

    def createField(self, name: str, oft: int):
        """Create field."""
        field = ogr.FieldDefn(name, oft)
        self.ogrLayer.CreateField(field)

    def createFeature(self, geometry: Geometry, **kwargs):
        """Create feature. Define attributes via **kwargs."""
        feature = ogr.Feature(self.ogrLayer.GetLayerDefn())
        for key, value in kwargs.items():
            feature.SetField(key, value)
        feature.SetGeometry(geometry.ogrGeometry)
        self.ogrLayer.CreateFeature(feature)

    def features(self, fieldNames: Sequence[str] = None) -> Iterator[Tuple[Geometry, Tuple]]:
        """Return iterator over feature geometries and field values."""
        if fieldNames is None:
            fieldNames = []
        fieldIndices = [self.ogrLayer.GetLayerDefn().GetFieldIndex(fieldName) for fieldName in fieldNames]
        feature: ogr.Feature
        for feature in self.ogrLayer:
            geometry = Geometry(wkt=feature.geometry().ExportToWkt())
            values = tuple(feature.GetField(index) for index in fieldIndices)
            yield geometry, values

    @property
    def geometries(self) -> Iterator[Geometry]:
        """Return iterator over feature geometries."""
        feature: ogr.Feature
        for feature in self.ogrLayer:
            yield Geometry(wkt=feature.geometry().ExportToWkt())

    def fieldValues(self, fieldNames: Sequence[str] = None) -> Iterator[Tuple]:
        """Return iterator over feature field values."""
        if fieldNames is None:
            fieldNames = []
        fieldIndices = [self.ogrLayer.GetLayerDefn().GetFieldIndex(fieldName) for fieldName in fieldNames]
        feature: ogr.Feature
        for feature in self.ogrLayer:
            values = tuple(feature.GetField(index) for index in fieldIndices)
            yield values

    @property
    def featureCount(self) -> int:
        """Return number of features."""
        return self.ogrLayer.GetFeatureCount()

    @property
    def fieldCount(self) -> int:
        """Return number of fields."""
        return self.ogrLayer.GetLayerDefn().GetFieldCount()

    @property
    def fieldNames(self) -> List[str]:
        """Return field names."""
        names = [self.ogrLayer.GetLayerDefn().GetFieldDefn(i).GetName() for i in range(self.fieldCount)]
        return names

    @property
    def fieldTypes(self) -> List[int]:
        """Return field types."""
        types = [self.ogrLayer.GetLayerDefn().GetFieldDefn(i).GetType() for i in range(self.fieldCount)]
        return types

    def fieldType(self, name: str) -> int:
        """Return field type."""
        return self.fieldTypes[self.fieldNames.index(name)]

    @property
    def fieldTypeNames(self):
        """Return field type names."""
        typeNames = [self.ogrLayer.GetLayerDefn().GetFieldDefn(i).GetTypeName() for i in range(self.fieldCount)]
        return typeNames

    def rasterize(
            self, grid: Grid, gdt: int = None, initValue: Number = 0, burnValue: Union[int, float] = 1,
            burnAttribute: str = None, allTouched=False, filterSQL: str = None, filename: str = None,
            gco: List[str] = None
    ) -> 'GdalRaster':
        from _classic.hubdsm.core.gdaldriver import GdalDriver
        assert isinstance(grid, Grid)
        if gdt is None:
            gdt = gdal.GDT_Float32
        driver = GdalDriver.fromFilename(filename=filename)
        filename = driver.prepareCreation(filename=filename)
        shape = grid.shape.withZ(1)
        gdalRaster = driver.createFromShape(shape=shape, gdt=gdt, grid=grid, filename=filename, gco=gco)
        gdalBand = gdalRaster.band(1)
        gdalBand.fill(value=initValue)
        gdalBand.rasterize(
            layer=self, burnValue=burnValue, burnAttribute=burnAttribute, allTouched=allTouched, filterSQL=filterSQL
        )
        return gdalRaster

    def fieldCalculator(self, name: str, oft: int, ufunc: Callable):
        self.createField(name=name, oft=oft)
        feature: ogr.Feature
        for feature in self.ogrLayer:
            value = ufunc(feature=feature)
            feature.SetField(name, value)
            self.ogrLayer.SetFeature(feature)
