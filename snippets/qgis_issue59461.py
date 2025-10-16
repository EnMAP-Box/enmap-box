# https://github.com/qgis/QGIS/issues/59461#issuecomment-3307474917
from osgeo import gdal

ds: gdal.Dataset = gdal.Open(r'D:\_tutorial\_\band.tif')
rb: gdal.Band = ds.GetRasterBand(1)
rb.SetScale(2.75e-05)
rb.SetOffset(-0.2)
