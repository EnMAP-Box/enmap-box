from enmapbox.exampledata import enmap, landcover_polygons, landcover_points
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedvectoralgorithm import \
    PrepareClassificationDatasetFromCategorizedVectorAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from testdata import points_in_no_data_region_gpkg


class TestPrepareClassificationSampleFromCategorizedVectorAlgorithm(TestCase):

    def test_styled_poly(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_polygons,
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

    def test_styled_point(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_points,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual((58, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4, 5], [c.value for c in dump.categories])
        self.assertListEqual(
            ['impervious', 'low vegetation', 'tree', 'soil', 'water'], [c.name for c in dump.categories]
        )

    def test_field_poly(self):
        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_VECTOR: landcover_polygons,
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
            alg.P_CATEGORIZED_VECTOR: landcover_polygons,
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
            alg.P_CATEGORIZED_VECTOR: points_in_no_data_region_gpkg,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((1, 177), dump.X.shape)
        self.assertEqual((1, 1), dump.y.shape)

    def test_issue1323(self):
        if not self.additionalDataFolderExists():
            return

        alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: r'D:\data\issues\1323\testing_emb_classification\X0061_Y0048_full_stack.vrt',
            alg.P_CATEGORIZED_VECTOR: r'D:\data\issues\1323\testing_emb_classification\queried_lucas.gpkg',
            alg.P_CATEGORY_FIELD: 'lc1',
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }

        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((1, 177), dump.X.shape)
        self.assertEqual((1, 1), dump.y.shape)
