import unittest

from osgeo import gdal

from enmapboxprocessing.algorithm.libraryfromregressiondatasetalgorithm import LibraryFromRegressionDatasetAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectoralgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap_potsdam, landcover_potsdam_point
from enmapboxtestdata import fraction_point_multitarget, fraction_point_singletarget, enmap, landcover_polygon
from qgis.core import QgsVectorLayer, QgsProcessingException


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
class TestPrepareRegressionDatasetFromContinuousVectorAlgorithm(TestCase):

    def test_styled_multitarget(self):

        alg = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CONTINUOUS_VECTOR: fraction_point_multitarget,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((51, 177), dump.X.shape)
        self.assertEqual((51, 6), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'], [t.name for t in dump.targets]
        )

        # check locations
        alg = LibraryFromRegressionDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_LIBRARY: self.filename('library.gpkg')
        }
        self.runalg(alg, parameters)
        self.assertEqual(
            384027,
            round(QgsVectorLayer(self.filename('library.gpkg')).getFeatures().__next__().geometry().asPoint().x())
        )

    def test_styled_singletarget(self):
        alg = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CONTINUOUS_VECTOR: fraction_point_singletarget,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((51, 177), dump.X.shape)
        self.assertEqual((51, 1), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual(
            ['vegetation'], [t.name for t in dump.targets]
        )

    def test_wrong_style(self):
        alg = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CONTINUOUS_VECTOR: landcover_polygon,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual(str(error), 'Select either a continuous-valued vector layer, or fields with targets.')

    def test_excludeBadBands(self):
        alg = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CONTINUOUS_VECTOR: landcover_potsdam_point,
            alg.P_TARGET_FIELDS: ['level_1', 'level_2'],
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(218, dump.X.shape[1])
        self.assertEqual(218, len(dump.features))

    def test_notExcludeBadBands(self):
        alg = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CONTINUOUS_VECTOR: landcover_potsdam_point,
            alg.P_TARGET_FIELDS: ['level_1', 'level_2'],
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(224, dump.X.shape[1])
        self.assertEqual(224, len(dump.features))
