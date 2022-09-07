import numpy as np

import processing
from enmapbox.exampledata import enmap
from enmapboxprocessing.algorithm.importlandsatl2algorithm import ImportLandsatL2Algorithm
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.test.testcase import TestCase
from qgis.PyQt.QtCore import QDateTime
from qgis.core import QgsRasterRange, QgsRasterLayer


class TestRasterReader(TestCase):

    def setUp(self):
        self.reader = RasterReader(enmap)
        self.provider = self.reader.provider
        self.array = self.reader.gdalDataset.ReadAsArray()

    def test_readFirstPixel(self):
        lead = self.reader.arrayFromPixelOffsetAndSize(xOffset=0, yOffset=0, width=1, height=1)
        gold = self.array[:, 0:1, 0:1]
        self.assertArrayEqual(lead, gold)

    def test_readLastPixel(self):
        lead = self.reader.arrayFromPixelOffsetAndSize(xOffset=3, yOffset=1, width=1, height=1)
        gold = self.array[:, 1:2, 3:4]
        self.assertArrayEqual(lead, gold)

    def test_readAllData(self):
        lead = self.reader.array()
        gold = self.array
        self.assertArrayEqual(lead, gold)

    def test_readAllData_withBoundingBox_andSize(self):
        array = np.array(self.reader.array(boundingBox=self.provider.extent(), width=22, height=40))
        self.assertEqual((177, 40, 22), array.shape)

    def test_readAllData_withBoundingBox_atNativeResolution(self):
        lead = self.reader.array(boundingBox=self.provider.extent())
        gold = self.array
        self.assertArrayEqual(lead, gold)

    def test_readAllData_withBoundingBox_atOversampledResolution(self):
        array = np.array(self.reader.array(boundingBox=self.provider.extent(), width=22, height=40))
        self.assertEqual((177, 40, 22), array.shape)

    def test_readEveryPixel_oneByOne(self):
        for xOffset in range(3):
            for yOffset in range(2):
                lead = self.reader.arrayFromPixelOffsetAndSize(xOffset, yOffset, width=1, height=1)
                gold = self.array[:, yOffset:yOffset + 1, xOffset:xOffset + 1]
                self.assertArrayEqual(lead, gold)

    def test_readWithOverlap(self):
        lead = self.reader.array(10, 10, self.reader.width() - 20, self.reader.height() - 20, overlap=10)
        gold = self.array
        self.assertArrayEqual(lead, gold)


class TestRasterMetadataReader(TestCase):

    def test_gdal_dataset_metadata(self):
        reader = RasterReader(enmap)
        gold = 'Micrometers'
        self.assertEqual(gold, reader.metadataItem('wavelength_units', 'ENVI'))
        self.assertEqual(gold, reader.metadataItem('wavelength units', 'ENVI'))
        self.assertEqual(gold, reader.metadataItem('wavelength_units'.upper(), 'ENVI'.lower()))
        self.assertEqual(gold, reader.metadataItem('wavelength units'.upper(), 'ENVI'.lower()))
        self.assertIsNone(reader.metadataItem('abc', 'XYZ'))

    def test_gdal_band_metadata(self):
        reader = RasterReader(enmap)
        self.assertEqual(reader.Micrometers, reader.wavelengthUnits(1))
        self.assertEqual(460.0, reader.wavelength(1))
        self.assertEqual(460.0, reader.wavelength(1, reader.Nanometers))
        self.assertEqual(0.460, reader.wavelength(1, reader.Micrometers))
        self.assertEqual(5.8, reader.fwhm(1))
        self.assertEqual(5.8, reader.fwhm(1, reader.Nanometers))
        self.assertEqual(0.0058, reader.fwhm(1, reader.Micrometers))

    def test_issue25(self):
        reader = RasterReader(r'C:\Users\Andreas\Downloads\Neuer Ordner\test\PRISMA_DESTRIPPED_AOIvAL.bsq')
        self.assertEqual('Nanometers', reader.wavelengthUnits(1))
        reader = RasterReader(r'C:\Users\Andreas\Downloads\Neuer Ordner\test\FX17_Test_2022-09-07_12-40-04.raw')
        self.assertEqual('Nanometers', reader.wavelengthUnits(1))

    def test_issue9(self):
        from testdata import force_1984_2021_060_319_HL_TSA_LNDLG_NDV_TSI_tif
        reader = RasterReader(force_1984_2021_060_319_HL_TSA_LNDLG_NDV_TSI_tif)
        self.assertEqual(QDateTime(1984, 3, 1, 0, 0), reader.startTime(1))
        self.assertEqual(QDateTime(1984, 3, 1, 0, 0), reader.centerTime(1))

        self.assertIsNone(reader.wavelength(1))
        self.assertIsNone(reader.wavelengthUnits(1))


class TestQgisPam(TestCase):
    # test QGIS PAM metadata handling (see #898)

    def test_item(self):
        layer = QgsRasterLayer(enmap)
        reader = RasterReader(layer)

        # make sure wavelength units exist in GDAL PAM
        key = 'wavelength_units'
        self.assertEqual('Micrometers', reader.gdalDataset.GetMetadataItem(key))

        # query wavelength units
        self.assertEqual('Micrometers', reader.metadataItem(key))

        # shadow GDAL PAM items
        reader.setMetadataItem(key, 'Nanometers')  # stores item in QGIS PAM
        self.assertEqual('Nanometers', reader.metadataItem(key))

        # shadow with None to effectively mask existing GDAL items
        reader.setMetadataItem(key, None)
        self.assertIsNone(None, reader.metadataItem(key))

        # ignoring QGIS PAM shadowing may be useful in some cases
        self.assertEqual('Micrometers', reader.metadataItem(key, ignoreQgisPam=True))

        # remove QGIS PAM item
        reader.removeMetadataItem(key)
        self.assertEqual('Micrometers', reader.metadataItem(key))  # ignoreQgisPam not required anymore

    def test_domain(self):
        layer = QgsRasterLayer(enmap)
        reader = RasterReader(layer)

        # make sure the ENVI domain exists
        domain = 'ENVI'
        domainItems = ['bands', 'band_names', 'byte_order', 'coordinate_system_string', 'data_ignore_value',
                       'data_type', 'default_bands', 'description', 'file_type', 'fwhm', 'header_offset', 'interleave',
                       'lines', 'samples', 'sensor_type', 'wavelength', 'wavelength_units', 'y_start', 'z_plot_titles']
        self.assertEqual(domainItems, list(reader.gdalDataset.GetMetadata(domain).keys()))

        # query domain
        self.assertEqual(
            domainItems,
            list(reader.metadataDomain(domain).keys())
        )

        # shadow GDAL PAM item in domain
        key = 'wavelength_units'
        reader.setMetadataItem(key, 'TEST', domain)
        self.assertEqual('TEST', reader.metadataDomain(domain)[key])

        # shadow with None to effectively mask existing GDAL items
        reader.setMetadataItem(key, None, domain)
        self.assertIsNone(reader.metadataDomain(domain)[key])

        # ignoring QGIS PAM shadowing may be useful in some cases
        self.assertEqual('Micrometers', reader.metadataDomain(domain, ignoreQgisPam=True)[key])

        # remove QGIS PAM domain
        reader.removeMetadataDomain(domain)
        self.assertEqual('Micrometers', reader.metadataItem(key))  # ignoreQgisPam not required anymore

    def test_domainList(self):
        layer = QgsRasterLayer(enmap)
        reader = RasterReader(layer)

        # make sure which GDAL domains exists
        self.assertEqual(
            ['IMAGE_STRUCTURE', '', 'ENVI', 'DERIVED_SUBDATASETS'],
            reader.gdalDataset.GetMetadataDomainList()
        )

        # query domain keys
        self.assertEqual(
            ['IMAGE_STRUCTURE', '', 'ENVI', 'DERIVED_SUBDATASETS'],
            reader.metadataDomainKeys()
        )

        # add item to a new domain
        reader.setMetadataItem('KEY', 'VALUE', 'NEW_DOMAIN')
        self.assertTrue('NEW_DOMAIN' in reader.metadataDomainKeys())

        # ignore QGIS PAM to ignore the new domain
        self.assertFalse('NEW_DOMAIN' in reader.metadataDomainKeys(ignoreQgisPam=True))

    def test_wavelength(self):
        layer = QgsRasterLayer(enmap)
        reader = RasterReader(layer)

        # make sure GDAL PAM wavelength are available
        wavelengths = [float(reader.gdalBand(bandNo).GetMetadataItem('wavelength'))
                       for bandNo in range(1, layer.bandCount() + 1)]
        self.assertEqual(
            [0.46, 0.465, 0.47, 0.475, 0.479, 0.484, 0.489, 0.494, 0.499, 0.503, 0.508, 0.513, 0.518, 0.523, 0.528,
             0.533, 0.538, 0.543, 0.549, 0.554, 0.559, 0.565, 0.57, 0.575, 0.581, 0.587, 0.592, 0.598, 0.604, 0.61,
             0.616, 0.622, 0.628, 0.634, 0.64, 0.646, 0.653, 0.659, 0.665, 0.672, 0.679, 0.685, 0.692, 0.699, 0.706,
             0.713, 0.72, 0.727, 0.734, 0.741, 0.749, 0.756, 0.763, 0.771, 0.778, 0.786, 0.793, 0.801, 0.809, 0.817,
             0.824, 0.832, 0.84, 0.848, 0.856, 0.864, 0.872, 0.88, 0.888, 0.896, 0.915, 0.924, 0.934, 0.944, 0.955,
             0.965, 0.975, 0.986, 0.997, 1.007, 1.018, 1.029, 1.04, 1.051, 1.063, 1.074, 1.086, 1.097, 1.109, 1.12,
             1.132, 1.144, 1.155, 1.167, 1.179, 1.191, 1.203, 1.215, 1.227, 1.239, 1.251, 1.263, 1.275, 1.287, 1.299,
             1.311, 1.323, 1.522, 1.534, 1.545, 1.557, 1.568, 1.579, 1.59, 1.601, 1.612, 1.624, 1.634, 1.645, 1.656,
             1.667, 1.678, 1.689, 1.699, 1.71, 1.721, 1.731, 1.742, 1.752, 1.763, 1.773, 1.783, 2.044, 2.053, 2.062,
             2.071, 2.08, 2.089, 2.098, 2.107, 2.115, 2.124, 2.133, 2.141, 2.15, 2.159, 2.167, 2.176, 2.184, 2.193,
             2.201, 2.21, 2.218, 2.226, 2.234, 2.243, 2.251, 2.259, 2.267, 2.275, 2.283, 2.292, 2.3, 2.308, 2.315,
             2.323, 2.331, 2.339, 2.347, 2.355, 2.363, 2.37, 2.378, 2.386, 2.393, 2.401, 2.409],
            wavelengths
        )

        # query wavelength via the RasterReader.wavelength
        wavelength = reader.wavelength(bandNo=42)
        self.assertEqual(685.0, wavelength)

        # check that we properly cached the wavelength
        defaultDomain = ''
        self.assertEqual(0.685, layer.customProperty(f'QGISPAM/band/42/{defaultDomain}/wavelength'))
        self.assertEqual('Micrometers', layer.customProperty(f'QGISPAM/band/42/{defaultDomain}/wavelength_units'))


class TestRasterMaskReader(TestCase):

    def setUp(self):
        self.array = np.array([[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]])
        filename = self.filename('test.bsq')
        Driver(filename).createFromArray(self.array)
        self.reader = RasterReader(filename)
        self.provider = self.reader.provider

    def test_without_noData(self):
        gold = np.full_like(self.array, True, dtype=bool)
        lead = self.reader.maskArray(self.array)
        self.assertArrayEqual(lead, gold)

    def test_withSource_noData(self):
        self.provider.setNoDataValue(bandNo=1, noDataValue=0)
        gold = np.full_like(self.array, True, dtype=bool)
        gold[0, 0, 0] = False
        lead = self.reader.maskArray(self.array)
        self.assertArrayEqual(lead, gold)

    def test_withUser_noData(self):
        self.provider.setUserNoDataValue(bandNo=1, noData=[
            QgsRasterRange(0, 0),  # add 0
            QgsRasterRange(1, 2, QgsRasterRange.IncludeMin),  # add 1
            QgsRasterRange(1, 2, QgsRasterRange.IncludeMax),  # add 2
            QgsRasterRange(2, 4, QgsRasterRange.Exclusive),  # add 3
        ])
        gold = np.full_like(self.array, True, dtype=bool)
        gold[0, 0, 0:4] = False
        lead = self.reader.maskArray(self.array)
        self.assertArrayEqual(lead, gold)

    def test_withSourceAndUser_noData(self):
        self.provider.setNoDataValue(bandNo=1, noDataValue=4)  # add 4
        self.provider.setUserNoDataValue(bandNo=1, noData=[
            QgsRasterRange(0, 0),  # add 0
            QgsRasterRange(1, 2, QgsRasterRange.IncludeMin),  # add 1
            QgsRasterRange(1, 2, QgsRasterRange.IncludeMax),  # add 2
            QgsRasterRange(2, 4, QgsRasterRange.Exclusive),  # add 3
        ])
        gold = np.full_like(self.array, True, dtype=bool)
        gold[0, 0, 0:5] = False
        lead = self.reader.maskArray(self.array)
        self.assertArrayEqual(lead, gold)


class TestDataScaling(TestCase):

    def test_toVrt(self):
        # import Landsat 8 spectral raster VRT which already has data scale and offset values
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LC08_L2SP_192023_20210724_20210730_02_T1\LC08_L2SP_192023_20210724_20210730_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2.vrt')
        }
        result = processing.run(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(-0.2, reader.bandOffset(1))
        self.assertEqual(2.75e-05, reader.bandScale(1))
        sum1 = np.sum(reader.array(bandList=[1]))

        # translate to another VRT
        alg = SaveRasterAsAlgorithm()
        parameters = {
            alg.P_RASTER: reader.layer,
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2_copy1.vrt')
        }
        result = processing.run(alg, parameters)
        reader2 = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(-0.2, reader2.bandOffset(1))
        self.assertEqual(2.75e-05, reader2.bandScale(1))
        sum2 = np.sum(reader.array(bandList=[1]))
        self.assertEqual(sum1, sum2)

    def test_toGTiff(self):
        # import Landsat 8 spectral raster VRT which already has data scale and offset values
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LC08_L2SP_192023_20210724_20210730_02_T1\LC08_L2SP_192023_20210724_20210730_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2.vrt')
        }
        result = processing.run(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(-0.2, reader.bandOffset(1))
        self.assertEqual(2.75e-05, reader.bandScale(1))
        sum1 = np.sum(reader.array(bandList=[1]))

        # translate to another GTiff
        alg = SaveRasterAsAlgorithm()
        parameters = {
            alg.P_RASTER: reader.layer,
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2_copy2.tif')
        }
        result = processing.run(alg, parameters)
        reader2 = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(2.75e-05, reader2.bandScale(1))  # GDAL Translate hasn't scaled the data!
        self.assertEqual(-0.2, reader2.bandOffset(1))
        sum2 = np.sum(reader.array(bandList=[1]))
        self.assertEqual(sum1, sum2)

    def test_scaleAnd_toGTiff(self):
        # import Landsat 8 spectral raster VRT which already has data scale and offset values
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LC08_L2SP_192023_20210724_20210730_02_T1\LC08_L2SP_192023_20210724_20210730_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2.vrt')
        }
        result = processing.run(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(-0.2, reader.bandOffset(5))
        self.assertEqual(2.75e-05, reader.bandScale(5))
        mean1 = np.mean(reader.array(bandList=[5]))

        # set scaling
        reader.setUserBandScale(100, 5)
        # reader.setUserBandOffset(123, 5)

        # translate to another GTiff
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: reader.layer,
            alg.P_BAND_LIST: [5],
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2_copy2.tif')
        }
        result = processing.run(alg, parameters)
        reader2 = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(2.75e-05 * 100, reader2.bandScale(1))  # GDAL Translate hasn't scaled the data!
        # self.assertEqual(-0.2 * 100 + 123, reader2.bandOffset(5))
        mean2 = np.mean(reader2.array())
        self.assertAlmostEqual(mean1 * 100, mean2, 3)

    def test_scaleAnd_toVrt(self):
        # import Landsat 8 spectral raster VRT which already has data scale and offset values
        alg = ImportLandsatL2Algorithm()
        parameters = {
            alg.P_FILE: r'D:\data\sensors\landsat\C2L2\LC08_L2SP_192023_20210724_20210730_02_T1\LC08_L2SP_192023_20210724_20210730_02_T1_MTL.txt',
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2.vrt')
        }
        result = processing.run(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(-0.2, reader.bandOffset(5))
        self.assertEqual(2.75e-05, reader.bandScale(5))
        mean1 = np.mean(reader.array(bandList=[5]))

        # set scaling
        reader.setUserBandScale(100, 5)
        # reader.setUserBandOffset(123, 5)

        # translate to another GTiff
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: reader.layer,
            alg.P_BAND_LIST: [5],
            alg.P_OUTPUT_RASTER: self.filename('landsat8L2C2_copy3.vrt')
        }
        result = processing.run(alg, parameters)
        reader2 = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertAlmostEqual(2.75e-05 * 100, reader2.bandScale(1), 3)  # GDAL Translate hasn't scaled the data!
        # self.assertEqual(-0.2 * 100 + 123, reader2.bandOffset(5))
        mean2 = np.mean(reader2.array())
        self.assertAlmostEqual(mean1 * 100, mean2, 3)
