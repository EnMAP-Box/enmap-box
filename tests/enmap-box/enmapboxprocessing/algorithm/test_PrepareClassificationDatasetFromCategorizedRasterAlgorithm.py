from qgis.core import QgsVectorLayer, QgsRasterLayer

from enmapboxprocessing.algorithm.libraryfromclassificationdatasetalgorithm import \
    LibraryFromClassificationDatasetAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedrasteralgorithm import \
    PrepareClassificationDatasetFromCategorizedRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap_potsdam
from enmapboxtestdata import landcover_polygon_30m, enmap


class TestPrepareClassificationDatasetFromCategorizedRasterAlgorithm(TestCase):

    def test_styled(self):
        alg = PrepareClassificationDatasetFromCategorizedRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_RASTER: landcover_polygon_30m,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((2028, 177), dump.X.shape)
        self.assertEqual((2028, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
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

    def test_byBand(self):
        alg = PrepareClassificationDatasetFromCategorizedRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_RASTER: landcover_polygon_30m,
            alg.P_CATEGORY_BAND: 0,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((2028, 177), dump.X.shape)
        self.assertEqual((2028, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual([1, 2, 3, 4, 5, 6], [c.value for c in dump.categories])
        self.assertListEqual(['1', '2', '3', '4', '5', '6'], [c.name for c in dump.categories])

    def test_byFirstRendererBand(self):
        alg = PrepareClassificationDatasetFromCategorizedRasterAlgorithm()
        print(QgsRasterLayer(enmap).renderer())
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CATEGORIZED_RASTER: enmap,  # this makes not much sense, but we allow it anyways
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((71158, 177), dump.X.shape)
        self.assertEqual((71158, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertEqual(1911, len(dump.categories))

    def test_excludeBadBands(self):
        alg = PrepareClassificationDatasetFromCategorizedRasterAlgorithm()
        print(QgsRasterLayer(enmap).renderer())
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CATEGORIZED_RASTER: enmap_potsdam,  # this makes not much sense, but we allow it anyways
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(218, dump.X.shape[1])
        self.assertEqual(218, len(dump.features))

    def test_notExcludeBadBands(self):
        alg = PrepareClassificationDatasetFromCategorizedRasterAlgorithm()
        print(QgsRasterLayer(enmap).renderer())
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CATEGORIZED_RASTER: enmap_potsdam,  # this makes not much sense, but we allow it anyways
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = ClassifierDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(224, dump.X.shape[1])
        self.assertEqual(224, len(dump.features))
