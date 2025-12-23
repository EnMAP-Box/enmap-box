from typing import Union, List

import numpy as np
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from _classic.hubdsm.algorithm.processingoptions import ProcessingOptions
from _classic.hubdsm.core.gdaldriver import GdalDriver
from _classic.hubdsm.core.raster import Raster


def convertRaster(
        raster: Raster, noDataValues: List[Union[float, int]] = None, gdalDataType: int = None, filename: str = None,
        co: List[str] = None, po=ProcessingOptions()
) -> Raster:
    '''
    Convert raster allows to perform several converion tasks at ones:

        a) fill masked areas with given noDataValues

        b) cast to given gdalDataType

    '''
    if noDataValues is None:
        noDataValues = [None] * len(raster.bands)
    if len(noDataValues) != len(raster.bands):
        raise ValueError('incorrect number of noDataValues')

    if gdalDataType is None:
        gdalDataType = raster.band(number=1).gdalBand.gdalDataType

    numpyDataType = GDALTypeCodeToNumericTypeCode(gdalDataType)

    driver = GdalDriver.fromFilename(filename=filename)
    outGdalRaster = driver.createRaster(
        grid=raster.grid, bands=len(raster.bands), gdt=gdalDataType, filename=filename,
        gco=co
    )

    subgrids = list(raster.grid.subgrids(shape=po.getShape(default=raster.grid.shape)))
    n = len(subgrids) * len(raster.bands)
    i = 1
    t0 = po.callbackStart(convertRaster.__name__)
    for subgrid in subgrids:
        for outGdalBand, array, maskArray, noDataValue in zip(
                outGdalRaster.bands, raster.iterArrays(grid=subgrid), raster.iterMaskArrays(grid=subgrid), noDataValues
        ):
            po.callbackProgress(i, n)
            i += 1
            # convert type
            if array.dtype != numpyDataType:
                array = array.astype(dtype=numpyDataType)
            # set noDataValue
            if noDataValue is not None:
                array[np.logical_not(maskArray)] = noDataValue
            # write
            outGdalBand.writeArray(array=array, grid=subgrid)
            outGdalBand.setNoDataValue(value=noDataValue)
    po.callbackFinish(convertRaster.__name__, t0=t0)
    return Raster.open(outGdalRaster)
