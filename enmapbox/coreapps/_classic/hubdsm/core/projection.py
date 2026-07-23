# from __future__ import annotations
from dataclasses import dataclass
from osgeo import osr


@dataclass(frozen=True)
class Projection(object):
    """Data structure for projections."""
    wkt: str

    def __post_init__(self):
        assert isinstance(self.wkt, str)

    def __eq__(self, other: 'Projection'):
        return bool(self.osrSpatialReference.IsSame(other.osrSpatialReference))

    @classmethod
    def fromEpsg(cls, epsg: int) -> 'Projection':
        """Create projection by given authority ID."""
        projection = osr.SpatialReference()
        projection.ImportFromEPSG(int(epsg))
        return Projection(wkt=projection.ExportToWkt())

    @property
    def osrSpatialReference(self) -> osr.SpatialReference:
        """Return osr.SpatialReference."""
        srs = osr.SpatialReference()
        srs.ImportFromWkt(self.wkt)
        return srs

WGS84_PROJECTION = Projection.fromEpsg(epsg=4326)
