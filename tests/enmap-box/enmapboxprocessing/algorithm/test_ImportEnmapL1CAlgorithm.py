from enmapboxprocessing.algorithm.importenmapl1calgorithm import ImportEnmapL1CAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from tests.enmapboxtestdata import SensorProducts, sensorProductsRoot


class TestImportEnmapL1CAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None:
            return

        alg = ImportEnmapL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('enmapL1C.vrt'),
        }

        result = self.runalg(alg, parameters)
        # self.assertEqual(
        #     68448, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float))
        # )
