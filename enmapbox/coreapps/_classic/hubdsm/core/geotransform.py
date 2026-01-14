# from __future__ import annotations
from dataclasses import dataclass
from typing import NamedTuple

from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.resolution import Resolution


@dataclass
class GeoTransform(object):
    ul: Location
    resolution: Resolution

    def __post_init__(self):
        assert isinstance(self.ul, Location)
        assert isinstance(self.resolution, Resolution)

    @classmethod
    def fromGdalGeoTransform(cls, gdalGeoTransform: 'GdalGeoTransform') -> 'GeoTransform':
        assert isinstance(gdalGeoTransform, GdalGeoTransform)
        return GeoTransform(ul=gdalGeoTransform.ul(), resolution=gdalGeoTransform.resolution())

    def gdalGeoTransform(self) -> 'GdalGeoTransform':
        return GdalGeoTransform(upperLeftX=self.ul.x, upperLeftY=self.ul.y,
            xResolution=self.resolution.x, yResolution=-self.resolution.y,
            rowRotation=0., columnRotation=0.)


class GdalGeoTransform(NamedTuple):
    upperLeftX: float
    xResolution: float
    rowRotation: float
    upperLeftY: float
    columnRotation: float
    yResolution: float

    def ul(self) -> Location:
        return Location(x=self.upperLeftX, y=self.upperLeftY)

    def resolution(self) -> Resolution:
        return Resolution(x=self.xResolution, y=abs(self.yResolution))
