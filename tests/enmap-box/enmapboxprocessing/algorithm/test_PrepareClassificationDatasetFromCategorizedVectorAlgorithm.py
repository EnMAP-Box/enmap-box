import unittest

from osgeo import gdal

from enmapboxprocessing.algorithm.libraryfromclassificationdatasetalgorithm import \
    LibraryFromClassificationDatasetAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedvectoralgorithm import \
    PrepareClassificationDatasetFromCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import points_in_no_data_region, enmap, landcover_polygon, landcover_point, enmap_potsdam, \
    landcover_potsdam_polygon
from qgis.core import QgsVectorLayer


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestPrepareClassificationDatasetFromCategorizedVectorAlgorithm(TestCase):

    def test_styled_poly(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_polygon,
            alg.P_MAJORITY_VOTING: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((2028, 177), dump.X.shape)
        self.assertEqual((2028, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4, 5, 6], [c.value for c in dump.categories])
        self.assertListEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'], [c.name for c in dump.categories]
        )

        # check locations
        alg = LibraryFromClassificationDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_LIBRARY: self.filename('library.gpkg')
        }
        self.runalg(alg, parameters)
        self.assertEqual(
            383997,
            round(QgsVectorLayer(self.filename('library.gpkg')).getFeatures().__next__().geometry().asPoint().x())
        )

    def test_styled_point(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_point,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual((58, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual((58, 2), dump.locations.shape)
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4, 5], [c.value for c in dump.categories])
        self.assertListEqual(
            ['impervious', 'low vegetation', 'tree', 'soil', 'water'], [c.name for c in dump.categories]
        )

        # check locations
        alg = LibraryFromClassificationDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_LIBRARY: self.filename('library.gpkg')
        }
        self.runalg(alg, parameters)
        self.assertEqual(
            385857,
            round(QgsVectorLayer(self.filename('library.gpkg')).getFeatures().__next__().geometry().asPoint().x())
        )

    def test_field_poly(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_polygon,
            alg.P_CATEGORY_FIELD: 'level_3',
            alg.P_MAJORITY_VOTING: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((2028, 177), dump.X.shape)
        self.assertEqual((2028, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4, 5, 6], [c.value for c in dump.categories])
        self.assertListEqual(
            ['low vegetation', 'pavement', 'roof', 'soil', 'tree', 'water'],
            [c.name for c in dump.categories]
        )

    def test_minimal_coverage(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_polygon,
            alg.P_COVERAGE: 100,  # pure pixel only
            alg.P_MAJORITY_VOTING: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((1481, 177), dump.X.shape)
        self.assertEqual((1481, 1), dump.y.shape)

    def test_sample_in_noDataRegion(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: points_in_no_data_region,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((1, 177), dump.X.shape)
        self.assertEqual((1, 1), dump.y.shape)

    def test_saveAsJson(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_polygon,
            alg.P_MAJORITY_VOTING: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.json')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump.fromFile(parameters[alg.P_OUTPUT_DATASET])
        self.assertEqual((2028, 177), dump.X.shape)
        self.assertEqual((2028, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4, 5, 6], [c.value for c in dump.categories])
        self.assertListEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'], [c.name for c in dump.categories]
        )

    def test_excludeBadBands(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CATEGORIZED_VECTOR: landcover_potsdam_polygon,
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(218, dump.X.shape[1])
        self.assertEqual(218, len(dump.features))

    def test_notExcludeBadBands(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CATEGORIZED_VECTOR: landcover_potsdam_polygon,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(224, dump.X.shape[1])
        self.assertEqual(224, len(dump.features))
