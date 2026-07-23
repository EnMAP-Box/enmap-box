# from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import numpy as np

from _classic.hubdsm.core.base import DataClassArray


@dataclass(frozen=True)
class Location(DataClassArray):
    x: float
    y: float

    def __post_init__(self):
        assert isinstance(self.x, (int, float))
        assert isinstance(self.y, (int, float))

    def equal(self, other: 'Location', tol: Optional[float]):
        """Compore self with other location with given tolerance."""

        assert isinstance(other, Location)
        if tol is None:
            tol = 1e-5
        return np.all(np.abs(np.subtract(self, other)) <= tol)
