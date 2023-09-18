import numpy as np

from enmapboxprocessing.algorithm.importdesisl1calgorithm import ImportDesisL1CAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import sensorProductsRoot, SensorProducts


class TestImportDesisL1CAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None:
            return

        alg = ImportDesisL1CAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Desis.L1C_MetadataXml,
            alg.P_OUTPUT_RASTER: self.filename('desisL1C.vrt'),
        }

        result = self.runalg(alg, parameters)
        self.assertEqual(-34916204544, round(np.sum(RasterReader(result[alg.P_OUTPUT_RASTER]).array(bandList=[1]))))
