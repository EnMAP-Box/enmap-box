from os.path import join
from pathlib import Path
from enmapbox import exampledata

root = Path(__file__).parents[1] / 'testdata'

# RASTER
_subdir = 'raster'

# - spectral raster
enmap = exampledata.enmap
hires = exampledata.hires

# - rasterized landcover polygons
landcover_polygon_1m = join(root, _subdir, 'landcover_polygon_1m.tif')
landcover_polygon_1m_3classes = join(root, _subdir, 'landcover_polygon_1m_3classes.tif')
landcover_polygon_1m_epsg3035 = join(root, _subdir, 'landcover_polygon_1m_EPSG3035.tif')
landcover_polygon_30m = join(root, _subdir, 'landcover_polygon_30m.tif')
landcover_polygon_30m_epsg3035 = join(root, _subdir, 'landcover_polygon_30m_EPSG3035.tif')

# - landcover maps (predicted by RF)
landcover_map_l2 = join(root, _subdir, 'landcover_map_l2.tif')
landcover_map_l3 = join(root, _subdir, 'landcover_map_l3.tif')

# - rasterized landcover polygon fractions
fraction_polygon_l3 = join(root, _subdir, 'fraction_polygon_l3.tif')

# - landcover fraction maps (predicted by RF)
fraction_map_l3 = join(root, _subdir, 'fraction_map_l3.tif')

# - binary water mask (derived from landcover map)
water_mask_30m = join(root, _subdir, 'water_mask_30m.tif')

# - 300m grid (same extent as 30m rasters)
enmap_grid_300m = join(root, _subdir, 'enmap_grid_300m.vrt')

# VECTOR
_subdir = 'vector'

# - landcover polygons
landcover_polygon = exampledata.landcover_polygon
landcover_polygon_3classes = join(root, _subdir, 'landcover_polygon_3classes.gpkg')
landcover_polygon_3classes_id = join(root, _subdir, 'landcover_polygon_3classes_id.gpkg')
landcover_polygon_3classes_epsg4326 = join(root, _subdir, 'landcover_polygon_3classes_EPSG4326.gpkg')

# - landcover points
landcover_point = exampledata.landcover_point
landcover_points_singlepart_epsg3035 = join(root, _subdir, 'landcover_point_singlepart_3035.gpkg')
landcover_points_multipart_epsg3035 = join(root, _subdir, 'landcover_point_multipart_3035.gpkg')

# - landcover fraction points
fraction_point_multitarget = join(root, _subdir, 'fraction_point_multitarget.gpkg')
fraction_point_singletarget = join(root, _subdir, 'fraction_point_singletarget.gpkg')

points_in_no_data_region = join(root, _subdir, 'points_in_no_data_region.gpkg')

# LIBRARY
_subdir = 'library'
library = join(root, _subdir, 'library.gpkg')
landsat8_srf = join(root, _subdir, 'landsat8_srf.gpkg')

# DATASET
_subdir = 'ml'

# - Classifier
classifierDumpPkl = join(root, _subdir, 'classifier.pkl')

# - Classification dataset
classificationDatasetAsGpkgVector = join(root, _subdir, 'classification_dataset.gpkg')
classificationDatasetAsCsvVector = join(root, _subdir, 'classification_dataset.csv')
classificationDatasetAsJsonFile = join(root, _subdir, 'classification_dataset.json')
classificationDatasetAsPklFile = join(root, _subdir, 'classification_dataset.pkl')
classificationDatasetAsForceFile = (
join(root, _subdir, 'force_classification_features.csv'), join(root, _subdir, 'force_classification_labels.csv'))

# - Regressor
regressorDumpPkl = join(root, _subdir, 'regressor.pkl')
regressorDumpSingleTargetPkl = join(root, _subdir, 'regressor_singletarget.pkl')
regressorDumpMultiTargetPkl = join(root, _subdir, 'regressor_multitarget.pkl')

# - Regression dataset
regressionDatasetAsJsonFile = join(root, _subdir, 'regression_dataset.json')
regressionDatasetAsPkl = join(root, _subdir, 'regression_dataset.pkl')

# engeomap testdata
_subdir = root / 'external' / 'engeomap'
engeomap_cubus_gamsberg_subset = _subdir / 'cubus_gamsberg_subset'
engeomap_gamsberg_field_library = _subdir / 'gamsberg_field_library'
engeomap_gamesberg_field_library_color_mod = _subdir / 'gamesberg_field_library_color_mod.csv'
