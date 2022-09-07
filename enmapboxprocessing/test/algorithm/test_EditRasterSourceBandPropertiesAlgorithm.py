from time import sleep

from osgeo import gdal

from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.editrastersourcebandpropertiesalgorithm import EditRasterSourceBandPropertiesAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.algorithm.testcase import TestCase
from qgis.PyQt.QtCore import QDateTime


class TestEditRasterSourceBandPropertiesAlgorithm(TestCase):

    def copyEnmap(self):
        # make a copy of enmap
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OFFSET: -9999,
            alg.P_CREATION_PROFILE: alg.GTiffFormat,
            alg.P_OUTPUT_RASTER: self.filename('enmap1.tif')
        }
        self.runalg(alg, parameters)

        sleep(1)
        return parameters[alg.P_OUTPUT_RASTER]

    def test_name(self):
        filename = self.copyEnmap()
        values = [f'B{i}' for i in range(177)]
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_NAMES: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(values, [reader.bandName(bandNo) for bandNo in reader.bandNumbers()])

    def test_wavelength(self):
        filename = self.copyEnmap()
        values = [i for i in range(177)]
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_WAVELENGTHS: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(values, [reader.wavelength(bandNo) for bandNo in reader.bandNumbers()])
        self.assertEqual(['Nanometers'] * 177, [reader.wavelengthUnits(bandNo) for bandNo in reader.bandNumbers()])

    def test_fwhm(self):
        filename = self.copyEnmap()
        values = [i for i in range(177)]
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_FWHMS: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(values, [reader.fwhm(bandNo) for bandNo in reader.bandNumbers()])
        self.assertEqual(['Nanometers'] * 177, [reader.wavelengthUnits(bandNo) for bandNo in reader.bandNumbers()])

    def test_badBandMultiplier(self):
        filename = self.copyEnmap()
        values = [1] * 177
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_BAD_BAND_MULTIPLIERS: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual([1] * 177, [reader.badBandMultiplier(bandNo) for bandNo in reader.bandNumbers()])

    def test_startTime(self):
        filename = self.copyEnmap()
        values = ['1999-12-31T12:30:59'] * 177
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_START_TIMES: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(
            [QDateTime(1999, 12, 31, 12, 30, 59)] * 177,
            [reader.startTime(bandNo) for bandNo in reader.bandNumbers()]
        )

    def test_unset_startTime(self):
        filename = self.copyEnmap()
        values = [''] * 177
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_START_TIMES: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(
            [None] * 177,
            [reader.startTime(bandNo) for bandNo in reader.bandNumbers()]
        )

    def test_endTime(self):
        filename = self.copyEnmap()
        values = ['1999-12-31T12:30:59'] * 177
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_END_TIMES: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(
            [QDateTime(1999, 12, 31, 12, 30, 59)] * 177,
            [reader.endTime(bandNo) for bandNo in reader.bandNumbers()]
        )

    def test_noDataValue(self):
        filename = self.copyEnmap()
        values = [-1234] * 177
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_NO_DATA_VALUES: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual([-1234] * 177, [reader.noDataValue(bandNo) for bandNo in reader.bandNumbers()])

    def test_offset(self):
        # filename = self.copyEnmap()
        filename = self.filename('enmap_uncompressed.tif')
        values = list(range(10000, 177 + 10000))
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_OFFSETS: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(values, [reader.bandOffset(bandNo) for bandNo in reader.bandNumbers()])

    def test_scale(self):
        filename = self.copyEnmap()
        # filename = self.filename('enmap_uncompressed.tif')
        values = [1.2345] * 177
        alg = EditRasterSourceBandPropertiesAlgorithm()
        parameters = {
            alg.P_SOURCE: filename,
            alg.P_SCALES: str(values),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(filename)
        self.assertListEqual(values, [reader.bandScale(bandNo) for bandNo in reader.bandNumbers()])

    def test_offset_bug(self):
        filename = self.copyEnmap()

        for i in range(1, 4):
            # check current value
            ds = gdal.Open(filename)
            rb = ds.GetRasterBand(i)
            print(rb.GetNoDataValue(), rb.GetOffset(), rb.GetScale(), '# original values')

            # set new value
            rb.SetNoDataValue(123)
            rb.SetOffset(456)
            rb.SetScale(789)
            print(rb.GetNoDataValue(), rb.GetOffset(), rb.GetScale(), '# new values')

        for i in range(1, 4):
            # reopen raster and check value
            # ds.FlushCache()
            del ds
            ds = gdal.Open(filename)
            rb = ds.GetRasterBand(i)
            print(rb.GetNoDataValue(), rb.GetOffset(), rb.GetScale(), '# new values are lost after re-opening')
