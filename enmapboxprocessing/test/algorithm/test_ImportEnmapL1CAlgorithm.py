import numpy as np

from enmapboxprocessing.algorithm.importenmapl1calgorithm import ImportEnmapL1CAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportEnmapL1CAlgorithm(TestCase):

    def test(self):
        alg = ImportEnmapL1CAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\enmap\L1C_Arcachon_3\ENMAP01-____L1C-DT000400126_20170218T110119Z_003_V000204_20200510T095443Z-METADATA.XML',
            alg.P_OUTPUT_RASTER: self.filename('enmapL1C.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(
            68448, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float))
        )
