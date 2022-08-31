import processing
from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase


class TestRasterReaderRfc2(TestCase):

    def test_rfc2(self):  # RFC 2: Spectral Properties
        reader = RasterReader(enmap)

        # get wavelength
        self.assertEqual(685.0, reader.wavelength(42))
        self.assertEqual(8.1, reader.fwhm(42))
        self.assertEqual(685.0, reader.wavelength(42, 'nanometers'))
        self.assertEqual(8.1, reader.fwhm(42, 'nanometers'))
        self.assertEqual(0.685, reader.wavelength(42, 'micrometers'))
        self.assertEqual(0.0081, reader.fwhm(42, 'micrometers'))
        self.assertEqual(0.000685, round(reader.wavelength(42, 'millimeters'), 6))
        self.assertEqual(0.000000685, round(reader.wavelength(42, 'meters'), 9))

        # get fwhm
        self.assertEqual(8.1, reader.fwhm(42))
        self.assertEqual(0.0081, reader.fwhm(42, 'micrometers'))

        # get bad band multiplier
        self.assertEqual(1, reader.badBandMultiplier(42))

        # find band by wavelength
        self.assertEqual(42, reader.findWavelength(685))

        # set wavelength
        reader.setWavelength(123.456, 42)
        self.assertEqual(123.456, reader.wavelength(42))
        reader.setWavelength(0.123456, 42, 'micrometers')
        self.assertEqual(123.456, reader.wavelength(42))

        # set wavelength and fwhm
        reader.setWavelength(123.456, 42, fwhm=9.999)
        self.assertEqual(123.456, reader.wavelength(42))
        self.assertEqual(9.999, reader.fwhm(42))

        # set bad band multiplier
        reader.setBadBandMultiplier(0, 42)
        self.assertEqual(0, reader.badBandMultiplier(42))

        # note that this isn't altering the layer source
        self.assertEqual(685.0, RasterReader(enmap).wavelength(42))
        self.assertEqual(8.1, RasterReader(enmap).fwhm(42))
        self.assertEqual(1, RasterReader(enmap).badBandMultiplier(42))

        # changes can be stored to new GDAL source by creating a VRT copy
        alg = SaveRasterAsAlgorithm()
        parameters = {
            alg.P_RASTER: reader.layer,
            alg.P_CREATION_PROFILE: alg.DefaultVrtCreationProfile,
            alg.P_COPY_METADATA: True,
            alg.P_OUTPUT_RASTER: self.filename('enmap.vrt')
        }
        result = processing.run(alg, parameters)
        reader2 = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(123.456, reader2.wavelength(42))
        self.assertEqual(9.999, reader2.fwhm(42))
        self.assertEqual(0, reader2.badBandMultiplier(42))
