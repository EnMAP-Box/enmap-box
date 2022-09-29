from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousrasteralgorithm import \
    PrepareRegressionDatasetFromContinuousRasterAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import fraction_polygon_l3


class TestPrepareRegressionDatasetFromContinuousRasterAlgorithm(TestCase):

    def test(self):
        alg = PrepareRegressionDatasetFromContinuousRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_CONTINUOUS_RASTER: fraction_polygon_l3,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump.fromDict(Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((2559, 177), dump.X.shape)
        self.assertEqual((2559, 6), dump.y.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])
        self.assertListEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'],
            [t.name for t in dump.targets]
        )
        self.assertListEqual(
            ['#e60000', '#9c9c9c', '#98e600', '#267300', '#a87000', '#0064ff'],
            [t.color for t in dump.targets]
        )
