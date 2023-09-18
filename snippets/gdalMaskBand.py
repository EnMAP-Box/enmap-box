import numpy as np
from osgeo import gdal

from enmapbox.exampledata import enmap

outfile = r'C:\Users\Andreas\Downloads\mask.tif'
format = 'GTiff'

indataset = gdal.Open(enmap, gdal.GA_ReadOnly)
gdal.SetConfigOption('GDAL_TIFF_INTERNAL_MASK', 'NO')
out_driver = gdal.GetDriverByName(format)
outdataset = out_driver.Create(outfile, indataset.RasterXSize, indataset.RasterYSize, indataset.RasterCount,
                               gdal.GDT_Int16)
outdataset.CreateMaskBand(gdal.GMF_PER_DATASET)

gt = indataset.GetGeoTransform()
outdataset.SetGeoTransform(gt)

prj = indataset.GetProjectionRef()
outdataset.SetProjection(prj)

for iBand in range(1, indataset.RasterCount + 1):
    inband = indataset.GetRasterBand(iBand)
    inmaskband = inband.GetMaskBand()

    outband = outdataset.GetRasterBand(iBand)
    outmaskband = outband.GetMaskBand()

    for i in range(inband.YSize - 1, -1, -1):
        scanline = inband.ReadAsArray(0, i, inband.XSize, 1, inband.XSize, 1)
        outband.WriteArray(scanline, 0, i)

        scanline = np.random.randint(0, 255 + 1, scanline.shape, np.uint8)
        outmaskband.WriteArray(scanline, 0, i)

# seams to work, but QGIS is crashing
