from os.path import dirname, join

root = join(dirname(dirname(__file__)), 'testdata')

# raster
enmap_uncompressed = join(root, 'enmap_uncompressed.tif')
landcover_raster_1m = join(root, 'landcover_raster_1m.tif')
landcover_raster_30m = join(root, 'landcover_raster_30m.tif')
landcover_raster_1m_epsg3035 = join(root, 'landcover_raster_1m_EPSG3035.tif')
landcover_raster_30m_epsg3035 = join(root, 'landcover_raster_30m_EPSG3035.tif')
landcover_raster_1m_3classes = join(root, 'landcover_raster_1m_3classes.tif')
landcover_map_l2 = join(root, 'landcover_map_l2.tif')
landcover_map_l3 = join(root, 'landcover_map_l3.tif')
fraction_polygons_l3 = join(root, 'fraction_polygons_l3.tif')
fraction_map_l3 = join(root, 'fraction_map_l3.tif')
water_mask_30m = join(root, 'water_mask_30m.tif')
grid_300m = join(root, 'grid_300m.vrt')

# vector
landcover_polygons_3classes = join(root, 'landcover_berlin_polygon_3classes.gpkg')
landcover_polygons_3classes_id = join(root, 'landcover_berlin_polygon_3classes_id.gpkg')
landcover_polygons_3classes_epsg4326 = join(root, 'landcover_berlin_polygon_3classes_EPSG4326.gpkg')
landcover_points_singlepart_epsg3035 = join(root, 'landcover_berlin_point_singlepart_3035.gpkg')
landcover_points_multipart_epsg3035 = join(root, 'landcover_berlin_point_multipart_3035.gpkg')
fraction_points = join(root, 'fraction_points.gpkg')
fraction_points_singletarget = join(root, 'fraction_points_singletarget.gpkg')

points_in_no_data_region = join(root, 'points_in_no_data_region.gpkg')

# library
library = join(root, 'library.gpkg')

# dataset (X, y)
classificationDatasetAsVector = join(root, 'classification_dataset.gpkg')
classificationDatasetAsCsv = join(root, 'classification_dataset.csv')
classificationDatasetAsPkl = join(root, 'classification_dataset.pkl')
# todo: regressionDatasetAsVector = join(root, 'classification_dataset.gpkg')
# todo: regressionDatasetAsCsv = join(root, 'classification_dataset.csv')
regressionDatasetAsPkl = join(root, 'regression_dataset.pkl')

# learner and dataset (X, y) as dump
classifierDumpPkl = join(root, 'classifier.pkl')
classifierDumpJson = join(root, 'classifier.pkl.json')
regressorDumpPkl = join(root, 'regressor.pkl')
regressorDumpSingleTargetPkl = join(root, 'regressor_singletarget.pkl')
regressorDumpMultiTargetPkl = join(root, 'regressor_multitarget.pkl')  #

# todo: regressorDumpJson = join(root, 'classifier.pkl.json')

# classification dataset (X, y) as FORCE text files
classificationSampleAsCsv = (join(root, 'force_features.csv'), join(root, 'force_labels.csv'))

# spectral response functions
landsat8_sectralResponseFunctionLibrary = join(root, 'landsat8_srf.gpkg')
