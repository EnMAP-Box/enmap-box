from osgeo import gdal

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.writestacheaderalgorithm import WriteStacHeaderAlgorithm
from enmapboxtestdata import enmap_potsdam


class TestWriteStacHeaderAlgorithm(TestCase):

    def test(self):
        gdal.CopyFile(enmap_potsdam, self.filename('raster.tif'))
        alg = WriteStacHeaderAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: self.filename('raster.tif')
        }
        self.runalg(alg, parameters)
