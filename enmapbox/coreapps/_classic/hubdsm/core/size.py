from dataclasses import dataclass

from _classic.hubdsm.core.base import DataClassArray


@dataclass(frozen=True)
class Size(DataClassArray):
    x: float
    y: float

    def __post_init__(self):
        assert isinstance(self.x, (int, float))
        assert isinstance(self.y, (int, float))
        assert self.x >= 0
        assert self.y >= 0

