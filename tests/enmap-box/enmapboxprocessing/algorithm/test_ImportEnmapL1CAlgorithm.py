import numpy as np

from enmapboxprocessing.algorithm.importenmapl1calgorithm import ImportEnmapL1CAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import SensorProducts


class TestImportEnmapL1CAlgorithm(TestCase):

    def test(self):
        alg = ImportEnmapL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('enmapL1C.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(
            68448, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float))
        )
