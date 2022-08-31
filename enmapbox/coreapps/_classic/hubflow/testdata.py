#import matplotlib
#matplotlib.use('QT4Agg')
#from matplotlib import pyplot
from tempfile import gettempdir
from os.path import join, exists
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from osgeo import gdal
from _classic.hubflow.core import *
import _classic.hubdc.progressbar
import enmapboxtestdata

overwrite = not True
progressBar = _classic.hubdc.progressbar.CUIProgressBar
outdir = join(gettempdir(), 'hubflow_testdata')

enmap = lambda: Raster(filename=enmapboxtestdata.enmap)
vector = lambda: Vector(filename=enmapboxtestdata.landcover_polygons)

vectorClassification = lambda: VectorClassification(filename=enmapboxtestdata.landcover_polygons,
                                                    classAttribute='level_2_id',
                                                    minOverallCoverage=0., minDominantCoverage=0.,
                                                    oversampling=5)
vectorRegression = lambda: VectorRegression(filename=enmapboxtestdata.landcover_polygons,
                                            regressionAttribute='level_2_id',
                                            noDataValue=0., dtype=np.uint8,
                                            minOverallCoverage=1.)
vectorMask = lambda: VectorMask(filename=enmapboxtestdata.landcover_polygons, invert=False)
vectorPoints = lambda: VectorClassification(filename=enmapboxtestdata.landcover_points, classAttribute='level_2_id')
enmapClassification = lambda overwrite=overwrite: Classification.fromClassification(filename=join(outdir, 'enmapLandCover.bsq'),
                                                                                    classification=vectorClassification(),
                                                                                    grid=enmap().grid(), overwrite=overwrite)

enmapFraction = lambda overwrite=overwrite: Fraction.fromClassification(filename=join(outdir, 'enmapFraction.bsq'),
                                                                        classification=vectorClassification(),
                                                                        grid=enmap().grid(), overwrite=overwrite)

enmapRegression = lambda overwrite=overwrite: Regression(filename=enmapFraction(overwrite=overwrite).filename())

enmapSample = lambda:Sample(raster=enmap(), mask=vector())
enmapClassificationSample = lambda: ClassificationSample(raster=enmap(), classification=enmapClassification(overwrite))
enmapFractionSample = lambda: FractionSample(raster=enmap(), fraction=enmapFraction(overwrite))
enmapRegressionSample = lambda: RegressionSample(raster=enmap(), regression=enmapRegression())


if __name__ == '__main__':
    print('hubflow testdata directory: ' + outdir)
