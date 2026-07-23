# from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import numpy as np

from _classic.hubdsm.core.base import DataClassArray


@dataclass(frozen=True)
class Resolution(DataClassArray):
    """Pixel resolution."""
    x: float
    y: float

    def __post_init__(self):
        assert isinstance(self.x, (int, float))
        assert isinstance(self.y, (int, float))
        assert self.x > 0, 'Resolution must be greater than 0'
        assert self.y > 0, 'Resolution must be greater than 0'

    def equal(self, other: 'Resolution', tol: Optional[float] = None) -> bool:
        """Return whether self is equal to other."""
        assert isinstance(other, Resolution)
        if tol is None:
            tol = 1e-5
        return np.all(np.abs(np.subtract(self, other)) <= tol)
