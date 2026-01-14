from typing import List, Callable

import numpy as np
from osgeo.gdal_array import NumericTypeCodeToGDALTypeCode

from _classic.hubdsm.algorithm.processingoptions import ProcessingOptions
from _classic.hubdsm.algorithm.utils import allOneProfile
from _classic.hubdsm.core.gdaldriver import GdalDriver
from _classic.hubdsm.core.raster import Raster


def aggregateBands(
        raster: Raster, aggregationFunction: Callable, filename: str = None,
        co: List[str] = None, po=ProcessingOptions()
) -> Raster:
    '''Aggregate over all bands.'''

    ones = np.reshape(np.array(allOneProfile(raster=raster)), (-1, 1, 1))
    numpyDataType = aggregationFunction(ones, axis=0).dtype
    if numpyDataType == bool:
        numpyDataType = np.uint8
    gdalDataType = NumericTypeCodeToGDALTypeCode(numpyDataType)

    driver = GdalDriver.fromFilename(filename=filename)
    outGdalRaster = driver.createRaster(
        grid=raster.grid, bands=1, gdt=gdalDataType, filename=filename, gco=co
    )

    subgrids = list(raster.grid.subgrids(shape=po.getShape(default=raster.grid.shape)))
    n = len(subgrids)
    i = 1
    t0 = po.callbackStart(aggregateBands.__name__)
    for subgrid in subgrids:
        po.callbackProgress(i, n)
        i += 1

        array3d = raster.readAsArray(grid=subgrid)
        array2d = aggregationFunction(array3d, axis=0)
        outGdalRaster.band(number=1).writeArray(array=array2d, grid=subgrid)
    po.callbackFinish(aggregateBands.__name__, t0=t0)
    return Raster.open(outGdalRaster)
