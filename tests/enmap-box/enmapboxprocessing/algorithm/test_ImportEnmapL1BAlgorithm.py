import numpy as np

from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxtestdata import SensorProducts


class TestImportEnmapL1BAlgorithm(TestCase):

    def test(self):
        alg = ImportEnmapL1BAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Enmap.L1B_MetadataXml,
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
