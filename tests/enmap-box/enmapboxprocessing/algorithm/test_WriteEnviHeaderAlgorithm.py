from osgeo import gdal
from qgis.core import QgsProcessingException

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.writeenviheaderalgorithm import WriteEnviHeaderAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxtestdata import enmap


class TestWriteEnviHeaderAlgorithm(TestCase):

    def test_tif(self):

        filename = self.filename('enmap.tif')
        ds1: gdal.Dataset = gdal.Open(enmap)
        gdal.Translate(filename, ds1)
        ds2: gdal.Dataset = gdal.Open(filename)

        reader = RasterReader(enmap)
        writer = RasterWriter(ds2)

        writer.setMetadata(reader.metadata())
        for i in range(ds1.RasterCount):
            writer.setMetadata(reader.metadata(i + 1), i + 1)
        writer.close()
        del ds1, ds2, reader, writer

        alg = WriteEnviHeaderAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: filename,
        }
        self.runalg(alg, parameters)
        with open(filename + '.hdr') as file:
            text = file.read()

        if 'fwhm = {6.0' in text:
            return  # skip test because of a value-rounding bug in GDAL

    def test_envi(self):

        filename = self.filename('enmap.bsq')
        ds1: gdal.Dataset = gdal.Open(enmap)
        gdal.Translate(filename, ds1, format='ENVI')
        ds2: gdal.Dataset = gdal.Open(filename)
        ds2.SetMetadata(ds1.GetMetadata())
        del ds1, ds2

        alg = WriteEnviHeaderAlgorithm()
        alg.initAlgorithm()
        parameters = {
            alg.P_RASTER: filename,
        }
        try:
            self.runalg(alg, parameters)
        except QgsProcessingException as error:
            self.assertEqual(str(error), 'Raster layer is not a GeoTiff')
