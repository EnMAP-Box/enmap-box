import numpy as np

from enmapboxprocessing.algorithm.importdesisl1calgorithm import ImportDesisL1CAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportDesisL1CAlgorithm(TestCase):

    def test(self):
        alg = ImportDesisL1CAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\desis\DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210\DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210-METADATA.xml',
            alg.P_OUTPUT_RASTER: self.filename('desisL1C.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(-34916204544, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]))))
