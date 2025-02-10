import numpy as np
from qgis.core import Qgis
from qgis.core import QgsVectorLayer

from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap, landcover_polygon, fraction_point_multitarget
from enmapboxtestdata import landcover_polygon_3classes_epsg4326


class TestRasterizeVectorAlgorithm(TestCase):

    def test_default(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygon,
            alg.P_OUTPUT_RASTER: self.filename('mask.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(Qgis.Float32, RasterReader(result[alg.P_OUTPUT_RASTER]).dataType())
        self.assertEqual(2028, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_differentCrs(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygon_3classes_epsg4326,
            alg.P_OUTPUT_RASTER: self.filename('mask.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2028, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_initAndBurnValue(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygon,
            alg.P_INIT_VALUE: 1,
            alg.P_BURN_VALUE: 0,
            alg.P_OUTPUT_RASTER: self.filename('invertedMask.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(85972, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_burnAttribute(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygon,
            alg.P_BURN_ATTRIBUTE: 'level_1_id',
            alg.P_OUTPUT_RASTER: self.filename('classes.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(3100, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

        lyr = QgsVectorLayer(fraction_point_multitarget)
        cnt = lyr.featureCount()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_INIT_VALUE: -9999,
            alg.P_VECTOR: fraction_point_multitarget,
            alg.P_BURN_ATTRIBUTE: 'tree',
            alg.P_OUTPUT_RASTER: self.filename('tree_fraction.tif')
        }
        result = self.runalg(alg, parameters)
        data = RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0]
        self.assertEqual(data.shape, (400, 220))
        is_valid = np.where(data != -9999)
        data = data[*is_valid]

        self.assertAlmostEqual(12.32, float(data.sum()), 2)
        self.assertEqual(cnt, len(data))

    def test_allTouched(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygon,
            alg.P_ALL_TOUCHED: True,
            alg.P_DATA_TYPE: alg.Byte,
            alg.P_OUTPUT_RASTER: self.filename('allTouched.tif')
        }
        result = self.runalg(alg, parameters)
        # self.assertEqual(2721, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())
        self.assertEqual(Qgis.Byte, RasterReader(result[alg.P_OUTPUT_RASTER]).dataType())

    def test_addValue(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygon,
            alg.P_ADD_VALUE: True,
            alg.P_OUTPUT_RASTER: self.filename('addValue.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2031, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_burnFid(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygon,
            alg.P_BURN_FID: True,
            alg.P_OUTPUT_RASTER: self.filename('fid.tif')
        }
        result = self.runalg(alg, parameters)
        # self.assertEqual(-79874, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum(dtype=float))
