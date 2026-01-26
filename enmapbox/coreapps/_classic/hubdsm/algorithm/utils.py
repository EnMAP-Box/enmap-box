from typing import List, Any

from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from _classic.hubdsm.core.raster import Raster


def allOneProfile(raster: Raster) -> List[Any]:
    assert isinstance(raster, Raster)
    profile = list()
    for band in raster.bands:
        dtype = GDALTypeCodeToNumericTypeCode(band.gdalBand.gdalDataType)
        profile.append(dtype(1))
    return profile
