from osgeo import gdal

from enmapboxtestdata import enmap_berlin

ds = gdal.Open(enmap_berlin)
R = ds.GetRasterBand(1)  # red
NIR = ds.GetRasterBand(4)  # nir

NDVI = (NIR - R) / (NIR + R)

gdal.GetDriverByName('VRT').CreateCopy('ndvi.vrt', NDVI)
