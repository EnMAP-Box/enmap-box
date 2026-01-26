# from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from _classic.hubdsm.core.base import DataClassArray
from _classic.hubdsm.core.coordinatetransformation import CoordinateTransformation
from _classic.hubdsm.core.geometry import Geometry
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.size import Size


@dataclass(frozen=True)
class Extent(DataClassArray):
    ul: Location
    size: Size

    def __post_init__(self):
        assert isinstance(self.ul, Location)
        assert isinstance(self.size, Size)

    @classmethod
    def fromGeometry(cls, geometry: Geometry) -> 'Extent':
        envelope = geometry.envelope
        return Extent(ul=envelope.ul, size=envelope.size)

    @property
    def geometry(self) -> Geometry:
        return Geometry.fromPolygonCoordinates(locations=[self.ul, self.ur, self.lr, self.ll])

    @property
    def xmin(self) -> float:
        return self.ul.x

    @property
    def xmax(self) -> float:
        return self.ul.x + self.size.x

    @property
    def ymin(self) -> float:
        return self.ul.y - self.size.y

    @property
    def ymax(self) -> float:
        return self.ul.y

    @property
    def ur(self) -> Location:
        return Location(x=self.xmax, y=self.ymax)

    @property
    def ll(self) -> Location:
        return Location(x=self.xmin, y=self.ymin)

    @property
    def lr(self) -> Location:
        return Location(x=self.xmax, y=self.ymin)

    def equal(self, other: 'Extent', tol: Optional[float] = None) -> bool:
        """Return wether self is almost equal to other."""
        assert isinstance(other, Extent)
        if tol is None:
            tol = 1e-5
        equal = abs(self.xmin - other.xmin) <= tol
        equal &= abs(self.xmax - other.xmax) <= tol
        equal &= abs(self.ymin - other.ymin) <= tol
        equal &= abs(self.ymax - other.ymax) <= tol
        return equal

    def within(self, other: 'Extent', tol: Optional[float] = None) -> bool:
        """Return wether self is almost inside other."""
        assert isinstance(other, Extent)
        if tol is None:
            tol = 1e-5
        assert isinstance(tol, float)
        result = True
        result &= other.xmin - tol < self.xmin
        result &= other.xmax + tol > self.xmax
        result &= other.ymin - tol < self.ymin
        result &= other.ymax + tol > self.ymax
        return result

    def intersection(self, other: 'Extent') -> 'Extent':
        assert isinstance(other, Extent)
        return Extent.fromGeometry(geometry=self.geometry.intersection(other.geometry))

    def union(self, other: 'Extent') -> 'Extent':
        assert isinstance(other, Extent)
        return Extent.fromGeometry(geometry=self.geometry.union(other.geometry))

    def reproject(self, coordinateTransformation=CoordinateTransformation) -> 'Extent':
        geometry = self.geometry.reproject(coordinateTransformation=coordinateTransformation)
        return Extent.fromGeometry(geometry=geometry)
