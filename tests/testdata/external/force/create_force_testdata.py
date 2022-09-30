# this script generates a small example
import pathlib

from osgeo import gdal

from enmapbox import DIR_UNITTESTS
from enmapbox.testing import start_app

PATH_SRC = pathlib.Path(r'D:\Temp\FORCE\1984-2021_060-319_HL_TSA_LNDLG_NDV_TSI.tif')

subsetX = [275, 285]
subsetY = [275, 290]
subsetZ = [1, 20]

assert PATH_SRC.is_file()
PATH_DST = pathlib.Path(DIR_UNITTESTS) / 'testdata' / 'force' / PATH_SRC.name
start_app()

bandList = list(range(subsetZ[0], subsetZ[1]))

toptions = gdal.TranslateOptions(
    srcWin=[subsetX[0], subsetY[0], subsetX[1] - subsetX[0], subsetY[1] - subsetY[0]],
    bandList=bandList)

dsSrc: gdal.Dataset = gdal.Open(PATH_SRC.as_posix())
gdal.Translate(PATH_DST.as_posix(), dsSrc, options=toptions)

dsDst = gdal.Open(PATH_DST.as_posix(), gdal.GA_Update)
domains = ['', 'FORCE']
for d in domains:
    md = dsSrc.GetMetadata(d)
    dsDst.SetMetadata(md, d)

for iB, b in enumerate(bandList):
    bandSrc: gdal.Band = dsSrc.GetRasterBand(iB + 1)
    bandDst: gdal.Band = dsDst.GetRasterBand(b)

    for d in domains:
        md = bandSrc.GetMetadata(d)
        bandDst.SetMetadata(md, d)

    bandDst.FlushCache()

dsDst.FlushCache()
del dsDst
