from enmapboxprocessing.algorithm.importenmapl1calgorithm import ImportEnmapL1CAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportEnmapL1CAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('enmapL1C.vrt'),
        }
        result = self.runalg(alg, parameters)

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('enmapL1C.tif'),
        }
        result = self.runalg(alg, parameters)
