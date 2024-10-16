from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportEnmapL1BAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL1BAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L1B_MetadataXml,
            alg.P_OUTPUT_VNIR_RASTER: self.filename('enmapL1BVnir.vrt'),
            alg.P_OUTPUT_SWIR_RASTER: self.filename('enmapL1BSwir.vrt'),
        }
        self.runalg(alg, parameters)

    def test_saveAsTif(self):
        if sensorProductsRoot() is None or self.skipProductImport:
            return

        alg = ImportEnmapL1BAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L1B_MetadataXml,
            alg.P_OUTPUT_VNIR_RASTER: self.filename('enmapL1BVnir.tif'),
            alg.P_OUTPUT_SWIR_RASTER: self.filename('enmapL1BSwir.tif'),
        }
        self.runalg(alg, parameters)
