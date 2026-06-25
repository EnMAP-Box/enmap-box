import unittest

from hzg_onns.core import onns

from enmapbox.apps.hzg_onns import OnnsProcessingAlgorithm
from enmapbox.testing import start_app, TestCase
from enmapboxtestdata import SensorProducts, sensorProductsRoot
from processing.core.Processing import Processing

start_app()


class ONNSTestCases(TestCase):

    @unittest.skipIf(not sensorProductsRoot(), 'No sensor products root')
    def test_onns_core(self):
        tmp = self.createTestOutputDirectory()

        inputfile = str(SensorProducts.Sentinel3.S3A_OL_2_WFR)
        outputfile = str(tmp / 'output.tif')

        alg = OnnsProcessingAlgorithm()

        cmd, output = onns(inputfile=inputfile,
                           outputDirectory=outputfile,
                           sensor=alg.SENSORS_ALGO[0],
                           adapt=0,
                           # 1 = C2R (default), 2 = POLYMER, 3 = IPF
                           ac=3,
                           # note that we deleted the insitu case!!!
                           osize=1)

    @unittest.skipIf(not sensorProductsRoot(), 'No sensor products root')
    def test_processing_algorithms(self):
        alg = OnnsProcessingAlgorithm()

        tmp = self.createTestOutputDirectory()

        path_s3 = SensorProducts.Sentinel3.S3A_OL_2_WFR

        param = {
            alg.P_FILE: str(path_s3),
            alg.P_OUTPUT_FOLDER: str(tmp)}

        Processing.runAlgorithm(alg, parameters=param)


if __name__ == '__main__':
    unittest.main()
