import numpy as np

from enmapboxprocessing.algorithm.importdesisl2aalgorithm import ImportDesisL2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from tests.enmapboxtestdata import sensorProductsRoot, SensorProducts


class TestImportDesisL2AAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None:
            return

        alg = ImportDesisL2AAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Desis.L2A_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('desisL2A.vrt'),
        }

        result = self.runalg(alg, parameters)
        self.assertEqual(
            -34920251152, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float))
        )
