import unittest

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.rasterizecategorizedvectoralgorithm import RasterizeCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap, landcover_polygon
from enmapboxtestdata import landcover_points_multipart_epsg3035, landcover_polygon_3classes_id, \
    landcover_polygon_3classes_epsg4326
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsPalettedRasterRenderer, QgsCategorizedSymbolRenderer


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestRasterizeCategorizedVectorAlgorithm(TestCase):

    def test_numberClassAttribute(self):
        alg = RasterizeCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: landcover_polygon_3classes_id,
            alg.P_GRID: enmap,
            alg.P_OUTPUT_CATEGORIZED_RASTER: self.filename('landcover_polygons.tif')
        }
        result = self.runalg(alg, parameters)
        classification = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])
        self.assertIsInstance(classification.renderer(), QgsPalettedRasterRenderer)
        vector = QgsVectorLayer(parameters[alg.P_CATEGORIZED_VECTOR])
        for c1, c2 in zip(
                Utils.categoriesFromCategorizedSymbolRenderer(vector.renderer()),
                Utils.categoriesFromPalettedRasterRenderer(classification.renderer())
        ):
            self.assertEqual((c1.name, c1.color), (c2.name, c2.color))

        self.assertEqual(1678, np.sum(RasterReader(result[alg.P_OUTPUT_CATEGORIZED_RASTER]).array()))

    def test_stringClassAttribute(self):
        alg = RasterizeCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: QgsVectorLayer(landcover_polygon),
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTPUT_CATEGORIZED_RASTER: self.filename('landcover_polygons.tif')
        }
        result = self.runalg(alg, parameters)
        classification = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])
        self.assertIsInstance(classification.renderer(), QgsPalettedRasterRenderer)
        for c1, c2 in zip(
                Utils.categoriesFromCategorizedSymbolRenderer(parameters[alg.P_CATEGORIZED_VECTOR].renderer()),
                Utils.categoriesFromPalettedRasterRenderer(classification.renderer())
        ):
            self.assertEqual((c1.name, c1.color), (c2.name, c2.color))
        self.assertEqual(5108, np.sum(RasterReader(result[alg.P_OUTPUT_CATEGORIZED_RASTER]).array()))

    def test_withNoneMatching_crs(self):
        alg = RasterizeCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: QgsVectorLayer(landcover_polygon_3classes_epsg4326),
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTPUT_CATEGORIZED_RASTER: self.filename('landcover_polygons.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(1678, np.sum(RasterReader(result[alg.P_OUTPUT_CATEGORIZED_RASTER]).array()))

    def test_pointVector(self):
        alg = RasterizeCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: QgsVectorLayer(landcover_points_multipart_epsg3035),
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTPUT_CATEGORIZED_RASTER: self.filename('landcover_points.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(152, np.sum(RasterReader(result[alg.P_OUTPUT_CATEGORIZED_RASTER]).array()))

    def test_minimalCoverage(self):
        alg = RasterizeCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: QgsVectorLayer(landcover_polygon),
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_COVERAGE: 100,
            alg.P_OUTPUT_CATEGORIZED_RASTER: self.filename('classification_fullcoverage.tif')
        }

        result = self.runalg(alg, parameters)
        self.assertEqual(3816, np.sum(RasterReader(result[alg.P_OUTPUT_CATEGORIZED_RASTER]).array()))

    def _test_issue1420(self):

        # change categories
        vector = QgsVectorLayer(landcover_polygon)
        renderer = vector.renderer()
        assert isinstance(renderer, QgsCategorizedSymbolRenderer)
        categories = Utils.categoriesFromRenderer(vector.renderer())
        categories = categories[:2]
        renderer = Utils.categorizedSymbolRendererFromCategories(renderer.classAttribute(), categories)
        vector.setRenderer(renderer)

        alg = RasterizeCategorizedVectorAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_CATEGORIZED_VECTOR: vector,
            alg.P_GRID: QgsRasterLayer(enmap),
            alg.P_OUTPUT_CATEGORIZED_RASTER: self.filename('classification.tif')
        }

        result = self.runalg(alg, parameters)
        raster = QgsRasterLayer(result[alg.P_OUTPUT_CATEGORIZED_RASTER])
        categories = Utils.categoriesFromRenderer(raster.renderer())
        self.assertEqual(2, len(categories))
