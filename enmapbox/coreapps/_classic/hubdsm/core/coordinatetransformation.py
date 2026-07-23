from dataclasses import dataclass
from osgeo import osr

from _classic.hubdsm.core.projection import Projection


@dataclass(frozen=True)
class CoordinateTransformation(object):
    """CoordinateTransformation."""
    source: Projection
    target: Projection

    def __post_init__(self):
        assert isinstance(self.source, Projection)
        assert isinstance(self.source, Projection)

    @property
    def osrCoordinateTransformation(self) -> osr.CoordinateTransformation:
        """Return osr.CoordinateTransformation."""
        return osr.CoordinateTransformation(self.source.osrSpatialReference, self.target.osrSpatialReference)
