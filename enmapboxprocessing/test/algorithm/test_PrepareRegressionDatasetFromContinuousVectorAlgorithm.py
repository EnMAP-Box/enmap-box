from qgis.core import QgsProcessingException

from enmapbox.exampledata import enmap, landcover_polygons, landcover_points
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedvectoralgorithm import \
    PrepareClassificationDatasetFromCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectoralgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import ClassifierDump, RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import points_in_no_data_region, fraction_points, fraction_points_singletarget


class TestPrepareRegressionDatasetFromCategorizedVectorAlgorithm(TestCase):

    def test_styled_multitarget(self):
        alg = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CONTINUOUS_VECTOR: fraction_points,
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

    def test_styled_singletarget(self):
        alg = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CONTINUOUS_VECTOR: fraction_points_singletarget,
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
            alg.P_CONTINUOUS_VECTOR: landcover_polygons,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual(str(error), 'Select either a continuous-valued vector layer, or fields with targets.')
