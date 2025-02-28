from qgis.core import QgsVectorLayer

from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.libraryfromregressiondatasetalgorithm import LibraryFromRegressionDatasetAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousrasteralgorithm import \
    PrepareRegressionDatasetFromContinuousRasterAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap_potsdam
from enmapboxtestdata import fraction_polygon_l3, enmap

start_app()


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

        # check locations
        filename = self.filename('library.gpkg')
        alg = LibraryFromRegressionDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: self.filename('sample.pkl'),
            alg.P_OUTPUT_LIBRARY: filename
        }
        self.runalg(alg, parameters)
        self.assertEqual(
            384147,
            round(QgsVectorLayer(filename).getFeatures().__next__().geometry().asPoint().x())
        )

    def test_excludeBadBands(self):
        alg = PrepareRegressionDatasetFromContinuousRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CONTINUOUS_RASTER: enmap_potsdam,  # this makes not much sense, but we allow it anyways
            alg.P_TARGETS: [1],
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(218, dump.X.shape[1])
        self.assertEqual(218, len(dump.features))

    def test_notExcludeBadBands(self):
        alg = PrepareRegressionDatasetFromContinuousRasterAlgorithm()
        parameters = {
            alg.P_FEATURE_RASTER: enmap_potsdam,
            alg.P_CONTINUOUS_RASTER: enmap_potsdam,  # this makes not much sense, but we allow it anyways
            alg.P_TARGETS: [1],
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_DATASET: self.filename('sample.pkl')
        }
        self.runalg(alg, parameters)
        dump = RegressorDump(**Utils.pickleLoad(parameters[alg.P_OUTPUT_DATASET]))
        self.assertEqual(224, dump.X.shape[1])
        self.assertEqual(224, len(dump.features))
