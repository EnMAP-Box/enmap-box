from enmapboxprocessing.algorithm.importemitl2aalgorithm import ImportEmitL2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import SensorProducts


class TestImportEmitL2AAlgorithm(TestCase):

    def test_allBands(self):
        alg = ImportEmitL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Emit.L2A_RFL,
            alg.P_SKIP_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('emitL2A_allBands.tif'),
        }

        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(285, RasterReader(parameters[alg.P_OUTPUT_RASTER]).bandCount())

    def test_goodBands(self):
        alg = ImportEmitL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Emit.L2A_RFL,
            alg.P_SKIP_BAD_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('emitL2A_goodBands.tif'),
        }

        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(244, RasterReader(parameters[alg.P_OUTPUT_RASTER]).bandCount())
