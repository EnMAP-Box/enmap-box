import unittest
from pathlib import Path

from enmapbox.testing import EnMAPBoxTestCase, start_app
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectoralgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAlgorithm

start_app()

DIR_DATA = Path(r'F:\Temp\OlgaSpang\SandPredictionTestS1S2Data')

path_shp = DIR_DATA / 'SmalTraining.shp'
path_tif = DIR_DATA / 'subset_S1S2_2024-01-21Clip.tif'


class TestIssue1083(EnMAPBoxTestCase):

    @unittest.skipIf(not path_shp.is_file() and path_tif.is_file(), 'Missing example data')
    def test_issue_1083(self):
        a = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        a.initAlgorithm({})

        tm_dir = self.createTestOutputDirectory()
        path_output = tm_dir / 'test_dataset.pkl'
        context, feedback = self.createProcessingContextFeedback()

        par = {a.P_CONTINUOUS_VECTOR: path_shp.as_posix(),
               a.P_TARGET_FIELDS: ['Sand'],
               a.P_FEATURE_RASTER: path_tif.as_posix(),
               a.P_OUTPUT_DATASET: path_output.as_posix()}
        a.run(par, context=context, feedback=feedback)

        self.assertTrue(path_output.is_file())
