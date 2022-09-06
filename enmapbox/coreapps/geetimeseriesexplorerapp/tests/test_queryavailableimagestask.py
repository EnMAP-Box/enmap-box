from unittest import TestCase

from qgis.gui import QgsMessageBar

import ee
from geetimeseriesexplorerapp.tasks.queryavailableimagestask import QueryAvailableImagesTask

ee.Initialize()


class TestQueryAvailableImagesTask(TestCase):

    def test(self):
        eePoint = ee.Geometry.Point([13.30033, 52.47824])
        eeCollection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterDate('2020-01-01', '2021-01-01',)
        task = QueryAvailableImagesTask(eeCollection, eePoint, 3, None)
        result = task.run()
        task.finished(result)
        self.assertEqual(
            "['Available Images', 'Acquisition Time', 'DATA_SOURCE_ELEVATION', 'WRS_TYPE', 'system:id', 'REFLECTANCE_ADD_BAND_1', 'REFLECTANCE_ADD_BAND_2', 'DATUM', 'REFLECTANCE_ADD_BAND_3', 'REFLECTANCE_ADD_BAND_4', 'REFLECTANCE_ADD_BAND_5', 'REFLECTANCE_ADD_BAND_6', 'REFLECTANCE_ADD_BAND_7', 'system:footprint', 'REFLECTIVE_SAMPLES', 'system:version', 'GROUND_CONTROL_POINTS_VERSION', 'SUN_AZIMUTH', 'DATA_SOURCE_TIRS_STRAY_LIGHT_CORRECTION', 'UTM_ZONE', 'DATE_ACQUIRED', 'ELLIPSOID', 'system:time_end', 'DATA_SOURCE_PRESSURE', 'LANDSAT_PRODUCT_ID', 'STATION_ID', 'TEMPERATURE_ADD_BAND_ST_B10', 'DATA_SOURCE_REANALYSIS', 'REFLECTANCE_MULT_BAND_7', 'system:time_start', 'REFLECTANCE_MULT_BAND_6', 'L1_PROCESSING_LEVEL', 'PROCESSING_SOFTWARE_VERSION', 'L1_DATE_PRODUCT_GENERATED', 'ORIENTATION', 'REFLECTANCE_MULT_BAND_1', 'WRS_ROW', 'REFLECTANCE_MULT_BAND_3', 'REFLECTANCE_MULT_BAND_2', 'TARGET_WRS_ROW', 'REFLECTANCE_MULT_BAND_5', 'REFLECTANCE_MULT_BAND_4', 'THERMAL_LINES', 'TIRS_SSM_POSITION_STATUS', 'GRID_CELL_SIZE_THERMAL', 'IMAGE_QUALITY_TIRS', 'TRUNCATION_OLI', 'NADIR_OFFNADIR', 'CLOUD_COVER', 'REQUEST_ID', 'EARTH_SUN_DISTANCE', 'TIRS_SSM_MODEL', 'COLLECTION_CATEGORY', 'SCENE_CENTER_TIME', 'GRID_CELL_SIZE_REFLECTIVE', 'SUN_ELEVATION', 'ALGORITHM_SOURCE_SURFACE_TEMPERATURE', 'TEMPERATURE_MAXIMUM_BAND_ST_B10', 'CLOUD_COVER_LAND', 'GEOMETRIC_RMSE_MODEL', 'ROLL_ANGLE', 'COLLECTION_NUMBER', 'DATE_PRODUCT_GENERATED', 'L1_REQUEST_ID', 'DATA_SOURCE_OZONE', 'SATURATION_BAND_1', 'DATA_SOURCE_WATER_VAPOR', 'SATURATION_BAND_2', 'SATURATION_BAND_3', 'IMAGE_QUALITY_OLI', 'SATURATION_BAND_4', 'LANDSAT_SCENE_ID', 'SATURATION_BAND_5', 'MAP_PROJECTION', 'SATURATION_BAND_6', 'SENSOR_ID', 'SATURATION_BAND_7', 'SATURATION_BAND_8', 'WRS_PATH', 'SATURATION_BAND_9', 'TARGET_WRS_PATH', 'L1_PROCESSING_SOFTWARE_VERSION', 'TEMPERATURE_MULT_BAND_ST_B10', 'L1_LANDSAT_PRODUCT_ID', 'PROCESSING_LEVEL', 'ALGORITHM_SOURCE_SURFACE_REFLECTANCE', 'GROUND_CONTROL_POINTS_MODEL', 'SPACECRAFT_ID', 'TEMPERATURE_MINIMUM_BAND_ST_B10', 'GEOMETRIC_RMSE_MODEL_Y', 'REFLECTIVE_LINES', 'GEOMETRIC_RMSE_MODEL_X', 'THERMAL_SAMPLES', 'system:asset_size', 'DATA_SOURCE_AIR_TEMPERATURE', 'system:index', 'system:bands', 'system:band_names']",
            str(task.header)
        )

    def test_empty(self):
        eePoint = ee.Geometry.Point([13.30033, 52.47824])
        eeCollection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterDate('2020-01-01', '2020-01-02',)
        task = QueryAvailableImagesTask(eeCollection, eePoint, 3, None)
        result = task.run()
        task.finished(result)
        self.assertEqual(0, len(task.data))
