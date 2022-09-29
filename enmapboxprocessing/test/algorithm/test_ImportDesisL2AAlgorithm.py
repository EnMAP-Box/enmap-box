import numpy as np

from enmapboxprocessing.algorithm.importdesisl2aalgorithm import ImportDesisL2AAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportDesisL2AAlgorithm(TestCase):

    def test(self):
        alg = ImportDesisL2AAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\desis\DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210\DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210-METADATA.xml',
            alg.P_OUTPUT_RASTER: self.filename('desisL2A.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(
            -34920251152, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float))
        )
