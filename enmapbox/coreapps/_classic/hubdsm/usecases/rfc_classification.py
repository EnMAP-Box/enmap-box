from osgeo import gdal
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from enmapbox.exampledata import enmap, hires, landcover_polygons
from _classic.hubdsm.algorithm.estimatorpredict import estimatorPredict
from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color
from _classic.hubdsm.core.raster import Raster

# prepare features (e.g. raster with different resolutions)
from _classic.hubdsm.core.rastercollection import RasterCollection

enmapRaster = Raster.open(enmap)
hiresRaster = Raster.open(hires)
featuresRaster = enmapRaster.addBands(hiresRaster)

# select grid for analysis (all date is resampled on-the-fly to this grid)
grid = enmapRaster.grid

# rasterize reference polygons
landcoverRaster = Raster.create(grid=grid, bands=1, gdt=gdal.GDT_Byte)
landcoverRaster.fill(value=0)
landcoverRaster.rasterize(layer=landcover_polygons, burnAttribute='level_2_id')
landcoverRaster.setNoDataValue(value=0)

# build raster collection and give more meaningful names
stack = RasterCollection(
    rasters=(
        landcoverRaster.withName(name='landcover'),
        featuresRaster.withName(name='features')
    )
)

# draw samples from raster collection
samples, location = stack.readAsSample(graRaster=gdal.GRA_Average, graMask=gdal.GRA_Mode, xMap='x', yMap='y')

# pretty print sample
for rasterName, sample in samples.items():
    print(rasterName)
    for fieldName in sample.dtype.names:
        print(f'  {fieldName}: {sample[fieldName]}')

# fit and apply RFC
y = samples['landcover'].array().ravel()
X = samples['features'].array().T
estimator = RandomForestClassifier(n_estimators=10, n_jobs=8)
estimator.fit(X=X, y=y)
classification = estimatorPredict(raster=featuresRaster, estimator=estimator, filename='data/rfc.bsq')

# set class colors and names
color = lambda hex: Color(*(int(hex[i:i + 2], 16) for i in (0, 2, 4)))
classification.setCategories(categories=[
    Category(id=1, name='impervious', color=color('e60000')),
    Category(id=2, name='low vegetation', color=color('98e600')),
    Category(id=3, name='tree', color=color('267300')),
    Category(id=4, name='soil', color=color('a87000')),
    Category(id=5, name='water', color=color('0064ff')),
])
