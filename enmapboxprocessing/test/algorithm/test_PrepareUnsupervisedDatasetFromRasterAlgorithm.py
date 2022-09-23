from enmapbox.exampledata import enmap, landcover_point
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromrasteralgorithm import \
    PrepareUnsupervisedDatasetFromRasterAlgorithm
from enmapboxprocessing.test.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import landcover_polygon_30m


class TestPrepareUnsupervisedDatasetFromRasterAlgorithm(TestCase):

    def test_noMask(self):
        alg = PrepareUnsupervisedDatasetFromRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((71158, 177), dump.X.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])

    def test_vectorMask(self):
        alg = PrepareUnsupervisedDatasetFromRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_MASK: landcover_point,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((58, 177), dump.X.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])

    def test_rasterMask(self):
        alg = PrepareUnsupervisedDatasetFromRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap,
            alg.P_MASK: landcover_polygon_30m,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual((2028, 177), dump.X.shape)
        self.assertEqual(177, len(dump.features))
        self.assertListEqual(['band 8 (0.460000 Micrometers)', 'band 9 (0.465000 Micrometers)'], dump.features[:2])

    def test_sampleSize(self):
        raise NotImplementedError()
