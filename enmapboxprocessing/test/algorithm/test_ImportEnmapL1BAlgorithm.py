import numpy as np

from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase


class TestImportEnmapL1BAlgorithm(TestCase):

    def test(self):
        alg = ImportEnmapL1BAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\enmap\L1B_Arcachon_3\ENMAP01-____L1B-DT000400126_20170218T110119Z_003_V000204_20200508T124425Z-METADATA.XML',
            alg.P_OUTPUT_VNIR_RASTER: self.filename('enmapL1BVnir.vrt'),
            alg.P_OUTPUT_SWIR_RASTER: self.filename('enmapL1BSwir.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        result = self.runalg(alg, parameters)
        self.assertEqual(
            49240, round(np.sum(RasterReader(result[alg.P_OUTPUT_VNIR_RASTER]).array(bandList=[1]), dtype=float))
        )
        self.assertEqual(
            15407, round(np.sum(RasterReader(result[alg.P_OUTPUT_SWIR_RASTER]).array(bandList=[1]), dtype=float))
        )
