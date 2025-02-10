from enmapbox.testing import EnMAPBoxTestCase, start_app
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectoralgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAlgorithm

start_app()


class TestIssue1083(EnMAPBoxTestCase):

    def test_issue_1083(self):
        a = PrepareRegressionDatasetFromContinuousVectorAlgorithm()
        a.initAlgorithm({})

        from enmapboxtestdata import fraction_point_multitarget, enmap_berlin
        tm_dir = self.createTestOutputDirectory()
        path_output = tm_dir / 'test_dataset.pkl'
        context, feedback = self.createProcessingContextFeedback()

        par = {a.P_CONTINUOUS_VECTOR: fraction_point_multitarget,
               a.P_TARGET_FIELDS: ['tree'],
               a.P_FEATURE_RASTER: enmap_berlin,
               a.P_OUTPUT_DATASET: path_output.as_posix()}
        a.run(par, context=context, feedback=feedback)

        self.assertTrue(path_output.is_file())
