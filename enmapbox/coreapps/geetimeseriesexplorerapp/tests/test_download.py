from time import time
from unittest import TestCase

from qgis._core import QgsVectorLayer

from geetimeseriesexplorerapp.geetemporalprofiledockwidget import DownloadTask
from tests.testdata import landcover_berlin_point_singlepart_3035_gpkg

locations = QgsVectorLayer(landcover_berlin_point_singlepart_3035_gpkg)

import ee
ee.Initialize()

class TestDownloadTask(TestCase):

    def test_downloadProfile(self):
        eePoint = ee.Geometry.Point([13.30033, 52.47824])
        eeCollection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").select('SR_B1')
        scale = 30
        offsets = [0]
        scales = [1]
        DownloadTask.downloadProfile((eePoint, eeCollection, scale, offsets, scales))

    def test_downloadProfiles(self):
        t0 = time()
        eePoints = [ee.Geometry.Point([13.30033, 52.47824])] * 100
        eeCollection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").select('SR_B1')
        DownloadTask.downloadProfiles(eePoints, eeCollection, scale=30, offsets=[0], scales=[1])
        #print(len(datas))
        print(round(time() - t0), 'sec')



"""
result_list = []
def log_result(result):
    # This is called whenever foo_pool(i) returns a result.
    # result_list is modified only by the main process, not the pool workers.
    result_list.append(result)

def apply_async_with_callback():
    pool = mp.Pool()
    for i in range(10):
        pool.apply_async(foo_pool, args = (i, ), callback = log_result)
    pool.close()
    pool.join()
    print(result_list)
"""