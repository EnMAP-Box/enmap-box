from osgeo import gdal

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.writestacheaderalgorithm import WriteStacHeaderAlgorithm
from enmapboxtestdata import enmap_potsdam


class TestWriteStacHeaderAlgorithm(TestCase):

    def test(self):
        driver: gdal.Driver = gdal.GetDriverByName('GTiff')
        driver.CopyFiles(self.filename('raster.tif'), enmap_potsdam)

        alg = WriteStacHeaderAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: self.filename('raster.tif')
        }
        self.runalg(alg, parameters)
