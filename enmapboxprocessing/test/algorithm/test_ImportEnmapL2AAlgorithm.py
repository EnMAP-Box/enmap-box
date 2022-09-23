import numpy as np

from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportEnmapL2AAlgorithm(TestCase):

    def test(self):
        alg = ImportEnmapL2AAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\enmap\L2A_Arcachon_3_combined\ENMAP01-____L2A-DT000400126_20170218T110119Z_003_V000204_20200512T142942Z-METADATA.XML',
            alg.P_OUTPUT_RASTER: self.filename('enmapL2A.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(
            -20444949162,
            np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]), dtype=float)
        )
