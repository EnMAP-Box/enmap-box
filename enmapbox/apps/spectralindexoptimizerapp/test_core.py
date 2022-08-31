import matplotlib
matplotlib.use('Qt5Agg')

import enmapboxtestdata
from spectralindexoptimizerapp.core import spectralIndexOptimizer
from _classic.hubdc.core import openRasterDataset

labels = openRasterDataset(filename=enmapboxtestdata.enmap).translate(filename='single.tif', bandList=[1]).filename()

spectralIndexOptimizer(
    filenamePrediction='prediction.tif',
    filenameReport='report.html',
    featuresFilename=enmapboxtestdata.enmap,
    labelsFilename='single.tif',
    rasterFilename=enmapboxtestdata.enmap,
    indexType=0,
    performanceType=0)
