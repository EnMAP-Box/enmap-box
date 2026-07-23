# from __future__ import annotations
from dataclasses import dataclass

from _classic.hubdsm.core.base import DataClassArray


@dataclass(frozen=True)
class GridShape(DataClassArray):
    y: int
    x: int

    def __post_init__(self):
        assert isinstance(self.y, int)
        assert isinstance(self.x, int)
        assert self.y > 0
        assert self.x > 0

    def withX(self, x: int) -> 'GridShape':
        return GridShape(y=self.y, x=x)

    def withY(self, y: int) -> 'GridShape':
        return GridShape(y=y, x=self.x)

    def withZ(self, z: int) -> 'RasterShape':
        return RasterShape(z=z, y=self.y, x=self.x)


@dataclass(frozen=True)
class RasterShape(DataClassArray):
    z: int
    y: int
    x: int

    def __post_init__(self):
        assert isinstance(self.z, int)
        assert isinstance(self.y, int)
        assert isinstance(self.x, int)
        assert self.z > 0
        assert self.y > 0
        assert self.x > 0

    @property
    def gridShape(self) -> GridShape:
        return GridShape(y=self.y, x=self.x)

    def withZ(self, z: int) -> 'RasterShape':
        return RasterShape(z=z, y=self.y, x=self.x)
