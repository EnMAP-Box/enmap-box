# from __future__ import annotations
from typing import List, NamedTuple
from dataclasses import dataclass

from osgeo import ogr

from _classic.hubdsm.core.coordinatetransformation import CoordinateTransformation
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.size import Size


@dataclass(frozen=True)
class Geometry(object):
    """Data structure for spatial geometries."""
    wkt: str

    def __post_init__(self):
        assert isinstance(self.wkt, str)
        ogrGeometry = self.ogrGeometry
        if ogrGeometry.ExportToWkt() != self.wkt:
            raise ValueError(f'invalid wkt format:\n{repr(self.wkt)}\nexpected:\n{repr(ogrGeometry.ExportToWkt())}')

    @staticmethod
    def formatWkt(wkt: str) -> str:
        ogrGeometry: ogr.Geometry = ogr.CreateGeometryFromWkt(wkt)
        if ogrGeometry is None:
            raise ValueError(f'invalid wkt: {repr(wkt)}')
        return ogrGeometry.ExportToWkt()

    @classmethod
    def fromLocation(cls, location: Location) -> 'Geometry':
        """Create point geometry."""
        wkt = f'POINT ({location.x} {location.y})'
        wkt = Geometry.formatWkt(wkt)
        return Geometry(wkt=wkt)

    @classmethod
    def fromPolygonCoordinates(cls, locations: List[Location]) -> 'Geometry':
        """Create polygon geometry."""
        assert len(locations) > 0
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for location in locations:
            assert isinstance(location, Location), location
            ring.AddPoint(location.x, location.y)
        if not locations[0] == locations[-1]:
            ring.AddPoint(*locations[0])
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        wkt = poly.ExportToWkt()
        wkt = Geometry.formatWkt(wkt)
        return Geometry(wkt=wkt)

    @property
    def ogrGeometry(self) -> ogr.Geometry:
        """Create ogr.Geometry object."""
        ogrGeometry = ogr.CreateGeometryFromWkt(self.wkt)
        assert ogrGeometry is not None
        return ogrGeometry

    @property
    def envelope(self) -> 'Envelope':
        """Returns envelope."""
        return Envelope(*self.ogrGeometry.GetEnvelope())

    @property
    def locations(self) -> List[Location]:
        """Return locations."""
        ogrGeometry = self.ogrGeometry
        name = ogrGeometry.GetGeometryName().lower()
        if name == ogr.GeometryTypeToName(ogr.wkbPoint).lower():
            locations = [self._locationsPoint(ogrGeometry=ogrGeometry)]
        elif name == ogr.GeometryTypeToName(ogr.wkbPolygon).lower():
            locations = self._locationsPolygon(ogrGeometry=ogrGeometry)
        else:
            raise TypeError(str(name))
        return locations

    @staticmethod
    def _locationsPoint(ogrGeometry: ogr.Geometry) -> Location:
        return Location(x=ogrGeometry.GetX(), y=ogrGeometry.GetY())

    @staticmethod
    def _locationsPolygon(ogrGeometry: ogr.Geometry) -> List[Location]:
        locations = list()
        for ring in ogrGeometry:
            for point in range(ring.GetPointCount()):
                x, y, z = ring.GetPoint(point)
                locations.append(Location(x=x, y=y))
        return locations

    def intersects(self, other: 'Geometry') -> bool:
        """Return whether self and other intersect."""
        assert isinstance(other, Geometry)
        return self.ogrGeometry.Intersects(other.ogrGeometry)

    def intersection(self, other: 'Geometry') -> 'Geometry':
        """Return intersection of self and other."""
        assert isinstance(other, Geometry)
        ogrGeometry = self.ogrGeometry.Intersection(other.ogrGeometry)
        return Geometry(wkt=ogrGeometry.ExportToWkt())

    def union(self, other: 'Geometry') -> 'Geometry':
        """Return union of self and other."""
        assert isinstance(other, Geometry)
        ogrGeometry = self.ogrGeometry.Union(other.ogrGeometry)
        return Geometry(wkt=ogrGeometry.ExportToWkt())

    def within(self, other: 'Geometry') -> bool:
        """Returns whether self is within other."""
        assert isinstance(other, Geometry)
        return self.ogrGeometry.Within(other.ogrGeometry)

    def reproject(self, coordinateTransformation: CoordinateTransformation) -> 'Geometry':
        """Reproject self."""
        ogrGeometry = self.ogrGeometry
        ogrGeometry.Transform(coordinateTransformation.osrCoordinateTransformation)
        wkt = ogrGeometry.ExportToWkt()
        wkt = Geometry.formatWkt(wkt)
        return Geometry(wkt=wkt)

    def buffer(self, distance: float) -> 'Geometry':
        """Buffered self."""
        wkt = self.ogrGeometry.Buffer(distance).ExportToWkt()
        wkt = Geometry.formatWkt(wkt=wkt)
        geometry = Geometry(wkt=wkt)
        return geometry


class Envelope(NamedTuple):
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    @property
    def ul(self) -> Location:
        return Location(x=self.xmin, y=self.ymax)

    @property
    def ur(self) -> Location:
        return Location(x=self.xmax, y=self.ymax)

    @property
    def lr(self) -> Location:
        return Location(x=self.xmax, y=self.ymin)

    @property
    def ll(self) -> Location:
        return Location(x=self.xmin, y=self.ymin)

    @property
    def size(self) -> Size:
        return Size(x=self.xmax - self.xmin, y=self.ymax - self.ymin)
