from enmapbox.exampledata import enmap, landcover_polygons
from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.core import Qgis
from testdata import landcover_berlin_polygon_3classes_EPSG4326_gpkg


class TestRasterizeAlgorithm(TestCase):

    def test_default(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygons,
            alg.P_OUTPUT_RASTER: self.filename('mask.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(Qgis.Float32, RasterReader(result[alg.P_OUTPUT_RASTER]).dataType())
        self.assertEqual(2028, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_differentCrs(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_berlin_polygon_3classes_EPSG4326_gpkg,
            alg.P_OUTPUT_RASTER: self.filename('mask.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2028, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_initAndBurnValue(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygons,
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
            alg.P_VECTOR: landcover_polygons,
            alg.P_BURN_ATTRIBUTE: 'level_1_id',
            alg.P_OUTPUT_RASTER: self.filename('classes.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(3100, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_allTouched(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygons,
            alg.P_ALL_TOUCHED: True,
            alg.P_DATA_TYPE: alg.Byte,
            alg.P_OUTPUT_RASTER: self.filename('allTouched.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2721, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())
        self.assertEqual(Qgis.Byte, RasterReader(result[alg.P_OUTPUT_RASTER]).dataType())

    def test_addValue(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygons,
            alg.P_ADD_VALUE: True,
            alg.P_OUTPUT_RASTER: self.filename('addValue.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(2031, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum())

    def test_burnFid(self):
        alg = RasterizeVectorAlgorithm()
        parameters = {
            alg.P_GRID: enmap,
            alg.P_VECTOR: landcover_polygons,
            alg.P_BURN_FID: True,
            alg.P_OUTPUT_RASTER: self.filename('fid.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(-79874, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0].sum(dtype=float))
