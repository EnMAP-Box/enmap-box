import processing
from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase


class TestRasterReaderRfc1(TestCase):

    def test_rfc1(self):  # RFC 1: Enhanced GDAL PAM for QGIS Raster Layers
        reader = RasterReader(enmap)

        # set new item to dataset-level default-domain
        reader.setMetadataItem('my key', 42)
        self.assertEqual(42, reader.metadataItem('my key'))

        # set new item to dataset-level user-domain
        reader.setMetadataItem('my key', 43, 'MY DOMAIN')
        self.assertEqual(43, reader.metadataItem('my key', 'MY DOMAIN'))

        # set new item to band-level default-domain
        reader.setMetadataItem('my key', 44, '', bandNo=1)
        self.assertEqual(44, reader.metadataItem('my key', '', bandNo=1))

        # set new item to band-level user-domain
        reader.setMetadataItem('my key', 45, 'MY DOMAIN', bandNo=1)
        self.assertEqual(45, reader.metadataItem('my key', 'MY DOMAIN', bandNo=1))

        # shadow item at dataset-level
        self.assertEqual('Micrometers', reader.metadataItem('wavelength units', 'ENVI'))
        reader.setMetadataItem('wavelength units', 'Nanometers', 'ENVI')
        self.assertEqual('Nanometers', reader.metadataItem('wavelength units', 'ENVI'))

        # shadow item at band-level
        self.assertEqual('Micrometers', reader.metadataItem('wavelength units', '', bandNo=1))
        reader.setMetadataItem('wavelength units', 'Nanometers', '', bandNo=1)
        self.assertEqual('Nanometers', reader.metadataItem('wavelength units', '', bandNo=1))

        # note that this isn't altering the layer source
        self.assertEqual('Micrometers', RasterReader(enmap).metadataItem('wavelength units', '', bandNo=1))

        # changes can be stored to new GDAL source by creating a VRT copy
        alg = SaveRasterAsAlgorithm()
        parameters = {
            alg.P_RASTER: reader.layer,
            alg.P_CREATION_PROFILE: alg.DefaultVrtCreationProfile,
            alg.P_COPY_METADATA: True,
            alg.P_OUTPUT_RASTER: self.filename('enmap.vrt')
        }
        result = processing.run(alg, parameters)
        self.assertEqual(
            'Nanometers',
            RasterReader(result[alg.P_OUTPUT_RASTER]).metadataItem('wavelength units', '', bandNo=1)
        )
