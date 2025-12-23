# from __future__ import annotations
from dataclasses import dataclass
from math import floor, ceil

from _classic.hubdsm.core.location import Location


@dataclass(frozen=True)
class PixelLocation(Location):
    """Subpixel location."""

    def __post_init__(self):
        assert isinstance(self.x, (int, float))
        assert isinstance(self.y, (int, float))

    @property
    def upperLeft(self) -> 'PixelLocation':
        """Pixel upper-left corner location."""
        return self.snap(func=floor)

    @property
    def lowerRight(self) -> 'PixelLocation':
        """Pixel lower-right corner location."""
        return self.snap(func=ceil)

    @property
    def center(self) -> 'PixelLocation':
        """Return the pixel center location."""
        return self.snap(func=lambda v: floor(v) + 0.5)

    @property
    def round(self) -> 'PixelLocation':
        """Return closest pixel corner location."""
        return self.snap(func=round)

    def snap(self, func) -> 'PixelLocation':
        """Return snapped pixel location."""
        return PixelLocation(x=func(self.x), y=func(self.y))
