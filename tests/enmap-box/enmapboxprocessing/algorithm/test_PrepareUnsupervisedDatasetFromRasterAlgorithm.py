import unittest

from osgeo import gdal

from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromrasteralgorithm import \
    PrepareUnsupervisedDatasetFromRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap_potsdam
from enmapboxtestdata import landcover_polygon_30m, enmap, landcover_point


@unittest.skipIf(gdal.VersionInfo().startswith('310'), 'Rasterize decimal error')
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

    def test_excludeBadBands(self):
        alg = PrepareUnsupervisedDatasetFromRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(218, dump.X.shape[1])
        self.assertEqual(218, len(dump.features))

    def test_notExcludeBadBands(self):
        alg = PrepareUnsupervisedDatasetFromRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = TransformerDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(224, dump.X.shape[1])
        self.assertEqual(224, len(dump.features))
