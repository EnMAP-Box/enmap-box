from enmapboxprocessing.algorithm.importsentinel2l2aalgorithm import ImportSentinel2L2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import sensorProductsRoot, SensorProducts


class TestImportSentinel2L2AAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportSentinel2L2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Sentinel2.S2B_L2A_MsiL1CXml,
            alg.P_OUTPUT_RASTER: self.filename('sentinel2L2A.vrt'),
        }
        self.runalg(alg, parameters)

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportSentinel2L2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Sentinel2.S2B_L2A_MsiL1CXml,
            alg.P_OUTPUT_RASTER: self.filename('sentinel2L2A_3.tif'),
        }
        self.runalg(alg, parameters)
