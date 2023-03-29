import numpy as np

from enmapboxprocessing.algorithm.importdesisl1balgorithm import ImportDesisL1BAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import sensorProductsRoot


class TestImportDesisL1BAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None:
            return

        alg = ImportDesisL1BAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\desis\DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210\DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210-METADATA.xml',
            alg.P_OUTPUT_RASTER: self.filename('desisL1B.vrt'),
        }

        result = self.runalg(alg, parameters)
        self.assertEqual(6298702, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]))))
