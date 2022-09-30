from enmapbox.exampledata import enmap, landcover_polygon
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectoralgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import fraction_point_multitarget, fraction_point_singletarget
from qgis.core import QgsProcessingException


class TestPrepareRegressionDatasetFromCategorizedVectorAlgorithm(TestCase):

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
