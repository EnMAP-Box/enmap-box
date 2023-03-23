from enmapboxprocessing.algorithm.importsentinel2l2aalgorithm import ImportSentinel2L2AAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase


class TestImportSentinel2L2AAlgorithm(TestCase):

    def test(self):
        alg = ImportSentinel2L2AAlgorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\sentinel2\S2A_MSIL2A_20200816T101031_N0214_R022_T32UQD_20200816T130108.SAFE\MTD_MSIL2A.xml',
            # alg.P_BAND_LIST: [1],
            alg.P_OUTPUT_RASTER: self.filename('sentinel2L2A.vrt'),
        }
        if not self.fileExists(parameters[alg.P_FILE]):
            return

        self.runalg(alg, parameters)
