from osgeo import gdal
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from enmapbox.exampledata import enmap, hires
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.resolution import Resolution

# use first three bands of EnMAP and the tree RGB bands from HyMap
enmapRaster = Raster.open(enmap).select([1, 2, 3])
hiresRaster = Raster.open(hires)

# stack bands together
stack = enmapRaster.addBands(hiresRaster)

# reverse bands
stack = stack[::-1]

# use EnMAP grid at 10m resolution
grid = enmapRaster.grid.withResolution(resolution=Resolution(x=10, y=10))
stack = stack.withGrid(grid=grid)

# save as VRT
vrt = stack.saveAsVrt(filename=r'data/stack.vrt', gra=gdal.GRA_Average)

# print some infos
print(vrt.grid.resolution)
for band in vrt.bands:
    print(band.name)
    print(f'  NoDataValue: {band.noDataValue}')
    print(f'  NumpyDataType: {GDALTypeCodeToNumericTypeCode(band.gdalBand.gdalDataType)}')
