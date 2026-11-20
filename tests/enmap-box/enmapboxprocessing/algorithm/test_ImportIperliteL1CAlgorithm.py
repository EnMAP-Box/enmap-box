from enmapboxprocessing.algorithm.importenmapl1calgorithm import ImportEnmapL1CAlgorithm
from enmapboxprocessing.algorithm.importiperlitel1calgorithm import ImportIperliteL1CAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportIperliteL1CAlgorithm(TestCase):

    def testUnzipped(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportIperliteL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Iperlite.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('iperliteL1C.vrt'),
        }
        self.runalg(alg, parameters)

    def testZipped(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportIperliteL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Iperlite.L1C_Zip,
            alg.P_OUTPUT_RASTER: self.filename('iperliteL1C.vrt'),
        }
        self.runalg(alg, parameters)

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Iperlite.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('iperliteL1C.tif'),
        }
        self.runalg(alg, parameters)
