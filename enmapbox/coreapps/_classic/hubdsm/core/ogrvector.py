# from __future__ import annotations
from dataclasses import dataclass
from typing import Union, Sequence

from osgeo import gdal, ogr, osr

from _classic.hubdsm.core.ogrlayer import OgrLayer
from _classic.hubdsm.core.projection import Projection, WGS84_PROJECTION


@dataclass(frozen=True)
class OgrVector(object):
    """OGR data source."""
    ogrDataSource: ogr.DataSource

    def __post_init__(self):
        assert isinstance(self.ogrDataSource, (ogr.DataSource, gdal.Dataset))

    @staticmethod
    def open(filename: str) -> 'OgrVector':
        assert isinstance(filename, str)
        ogrDataSource = gdal.OpenEx(filename, gdal.OF_VECTOR)
        assert isinstance(ogrDataSource, (ogr.DataSource, gdal.Dataset))
        return OgrVector(ogrDataSource=ogrDataSource)

    @property
    def filename(self) -> str:
        return self.ogrDataSource.GetDescription()

    def layer(self, nameOrIndex: Union[int, str] = None) -> OgrLayer:
        if nameOrIndex is None:
            nameOrIndex = 0
        if isinstance(nameOrIndex, int):
            return OgrLayer(ogrLayer=self.ogrDataSource.GetLayerByIndex(nameOrIndex), ogrDataSource=self.ogrDataSource)
        else:
            return OgrLayer(ogrLayer=self.ogrDataSource.GetLayerByName(nameOrIndex), ogrDataSource=self.ogrDataSource)

    def createLayer(
            self, name: str = '', projection: Projection = WGS84_PROJECTION, geometryType: int = None
    ) -> OgrLayer:
        """Create OGR layer with given name, projection and geometry type."""
        assert isinstance(name, str)
        assert isinstance(projection, Projection)
        if geometryType is None:
            geometryType = ogr.wkbNone
        assert isinstance(geometryType, int)
        srs = osr.SpatialReference(projection.wkt)
        ogrLayer = self.ogrDataSource.CreateLayer(name=name, srs=srs, geom_type=geometryType)
        return OgrLayer(ogrLayer=ogrLayer, ogrDataSource=self.ogrDataSource)

    def copyLayer(self, layer: OgrLayer, name: str = None, fieldNames: Sequence[str] = None) -> OgrLayer:
        """Copy OGR layer geometries and fields (optional)."""
        assert isinstance(layer, OgrLayer)
        if name is None:
            name = layer.name
        assert isinstance(name, str)
        if fieldNames is None:
            fieldNames = []
        layer2 = self.createLayer(name=name, projection=layer.projection, geometryType=layer.geometryType)
        fieldIndices = list()
        for fieldName in fieldNames:
            layer2.createField(name=fieldName, oft=layer.fieldType(name=fieldName))
            fieldIndices.append(layer.fieldNames.index(fieldName))

        feature: ogr.Feature
        for feature in layer.ogrLayer:
            featureCopy = ogr.Feature(layer2.ogrLayer.GetLayerDefn())
            for fieldName, fieldIndex in zip(fieldNames, fieldIndices):
                featureCopy.SetField(fieldName, feature.GetField(fieldIndex))
            geometry = feature.GetGeometryRef().Clone()
            featureCopy.SetGeometry(geometry)
            layer2.ogrLayer.CreateFeature(featureCopy)

        return layer2
