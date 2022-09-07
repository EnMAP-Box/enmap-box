from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.predictregressionalgorithm import PredictRegressionAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from testdata import regressorDumpPkl, regressorDumpSingleTargetPkl


class TestPredictRegressionAlgorithm(TestCase):

    def test_predict_multiTarget(self):
        alg = PredictRegressionAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpPkl,
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_REGRESSION: self.filename('regression.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_REGRESSION])
        self.assertEqual(
            ['#e60000', '#9c9c9c', '#98e600', '#267300', '#a87000', '#0064ff'],
            [reader.bandColor(bandNo).name() for bandNo in reader.bandNumbers()]
        )
        self.assertEqual(
            ['roof', 'pavement', 'low vegetation', 'tree', 'soil', 'water'],
            [reader.bandName(bandNo) for bandNo in reader.bandNumbers()]
        )

    def test_predict_singleTarget(self):
        alg = PredictRegressionAlgorithm()
        parameters = {
            alg.P_REGRESSOR: regressorDumpSingleTargetPkl,
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_REGRESSION: self.filename('regression.tif')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_REGRESSION])
        self.assertEqual(
            ['#98e600'],
            [reader.bandColor(bandNo).name() for bandNo in reader.bandNumbers()]
        )
        self.assertEqual(
            ['vegetation'],
            [reader.bandName(bandNo) for bandNo in reader.bandNumbers()]
        )
