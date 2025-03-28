from os.path import exists

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap, hires
from enmapboxtestdata import water_mask_30m, enmap_grid_300m
from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, QgsRasterLayer, QgsRasterRenderer, Qgis


class TestTranslateAlgorithm(TestCase):

    def test_default(self):
        writer = self.rasterFromRange((3, 10, 10))
        writer.close()

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        self.assertArrayEqual(
            RasterReader(parameters[alg.P_RASTER]).array(),
            RasterReader(parameters[alg.P_OUTPUT_RASTER]).array(),
        )

    def test_bandList(self):
        writer = self.rasterFromRange((3, 10, 10))
        writer.close()

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_BAND_LIST: [1],
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        # self.assertArrayEqual(
        #    RasterReader(parameters[alg.P_RASTER]).array()[1],
        #    RasterReader(parameters[alg.P_OUTPUT_RASTER]).array(),
        # )

    def test_grid_with_differentResolution_and_sameExtentAndCrs(self):
        crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        writerRaster = self.rasterFromRange((1, 3, 3), None, QgsRectangle(0, 0, 3, 3), crs)
        writerRaster.close()
        writerGrid = self.rasterFromRange((1, 1, 1), None, QgsRectangle(0, 0, 3, 3), crs)
        writerGrid.close()
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writerRaster.source(),
            alg.P_GRID: writerGrid.source(),
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        self.assertEqual(
            RasterReader(parameters[alg.P_RASTER]).array()[0][1, 1],
            RasterReader(parameters[alg.P_OUTPUT_RASTER]).array()[0][0, 0],
        )

    def test_grid_with_differentExtent_and_sameResolutionAndCrs(self):
        crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        writerRaster = self.rasterFromRange((1, 3, 3), None, QgsRectangle(0, 0, 3, 3), crs)
        writerRaster.close()
        writerGrid = self.rasterFromRange((1, 1, 1), None, QgsRectangle(1, 1, 2, 2), crs)
        writerGrid.close()
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writerRaster.source(),
            alg.P_GRID: writerGrid.source(),
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        self.assertEqual(
            RasterReader(parameters[alg.P_RASTER]).array()[0][1, 1],
            RasterReader(parameters[alg.P_OUTPUT_RASTER]).array()[0][0, 0],
        )

    def test_grid_with_differentExtentAndCrs(self):
        crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        extent = QgsRectangle(0, 0, 3, 3)
        writerRaster = self.rasterFromRange((1, 3, 3), None, extent, crs)
        writerRaster.close()
        crs2 = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        extent2 = Utils.transformExtent(extent, crs, crs2)
        writerGrid = self.rasterFromRange((1, 3, 3), None, extent2, crs2)
        writerGrid.close()
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writerRaster.source(),
            alg.P_GRID: writerGrid.source(),
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        self.assertEqual(extent2, RasterReader(parameters[alg.P_OUTPUT_RASTER]).extent())
        self.assertEqual(crs2, RasterReader(parameters[alg.P_OUTPUT_RASTER]).crs())
        self.assertArrayEqual(
            RasterReader(parameters[alg.P_RASTER]).array(),
            RasterReader(parameters[alg.P_OUTPUT_RASTER]).array()
        )

    def test_grid_with_differentExtentAndCrs_andBandSubset(self):
        crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        extent = QgsRectangle(0, 0, 3, 3)
        writerRaster = self.rasterFromRange((3, 3, 3), None, extent, crs)
        writerRaster.close()
        crs2 = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        extent2 = Utils.transformExtent(extent, crs, crs2)
        writerGrid = self.rasterFromRange((1, 3, 3), None, extent2, crs2)
        writerGrid.close()
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writerRaster.source(),
            alg.P_GRID: writerGrid.source(),
            alg.P_BAND_LIST: [2],
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        self.assertEqual(extent2, RasterReader(parameters[alg.P_OUTPUT_RASTER]).extent())
        self.assertEqual(crs2, RasterReader(parameters[alg.P_OUTPUT_RASTER]).crs())
        self.assertArrayEqual(
            RasterReader(parameters[alg.P_RASTER]).array()[1],
            RasterReader(parameters[alg.P_OUTPUT_RASTER]).array()[0]
        )

    def test_copyMetadata(self):
        writer = self.rasterFromRange((3, 3, 3))
        writer.setMetadataItem('my key', 'hello', '')
        writer.setMetadataItem('my key', 'world', '', 1)
        writer.close()
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: writer.source(),
            alg.P_COPY_METADATA: True,
            alg.P_OUTPUT_RASTER: self.filename('raster.vrt')
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        self.assertEqual('hello', reader.metadataItem('my key', ''))
        self.assertEqual('world', reader.metadataItem('my key', '', 1))

    def test_issue(self):
        ds: gdal.Dataset = gdal.Translate(self.filename('raster.vrt'), enmap)
        rb: gdal.Band = ds.GetRasterBand(1)
        rb.SetMetadata({}, '')
        rb: gdal.Band = ds.GetRasterBand(2)
        rb.SetMetadata({}, '')

    def test_dataType(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_BAND_LIST: [1],
            alg.P_CREATION_PROFILE: alg.GTiffFormat,
            alg.P_OUTPUT_RASTER: self.filename('raster.tif')
        }
        gold = [1, 3, 2, 4, 5, 6, 7]
        for index, name in enumerate(alg.O_DATA_TYPE):
            parameters[alg.P_DATA_TYPE] = index
            parameters[alg.P_OUTPUT_RASTER] = self.filename(f'raster.{name}.tif')
            result = self.runalg(alg, parameters)
            dataType = RasterReader(result[alg.P_OUTPUT_RASTER]).dataType()
            print(name, dataType)
            self.assertEqual(gold[index], dataType)

    def test_copyMetadata_forEnviSource_bandSubset(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_BAND_LIST: [3],
            alg.P_COPY_METADATA: True,
            alg.P_CREATION_PROFILE: alg.DefaultGTiffCreationProfile,
            alg.P_OUTPUT_RASTER: self.filename('enmap.tif')
        }
        result = self.runalg(alg, parameters)

        raster = RasterReader(result[alg.P_OUTPUT_RASTER])
        # self.assertEqual(raster.Nanometers, raster.wavelengthUnits(1))

        if raster.fwhm(1) == 6.0:
            return  # skip test because of a value-rounding bug in GDAL

        self.assertEqual(470, int(raster.wavelength(1)))
        self.assertEqual(raster.fwhm(1), 5.8)
        self.assertEqual(1, raster.badBandMultiplier(1))

    def test_copyMetadata2(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_COPY_METADATA: True,
            alg.P_CREATION_PROFILE: alg.DefaultGTiffCreationProfile,
            alg.P_OUTPUT_RASTER: self.filename('enmap.tif')
        }
        result = self.runalg(alg, parameters)

    def test_clipSourceGrid_byFullExtent(self):
        raster = QgsRasterLayer(enmap)
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: raster,
            alg.P_BAND_LIST: [1],
            alg.P_EXTENT: raster.extent(),
            alg.P_OUTPUT_RASTER: self.filename('enmapClipFull.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(raster.extent(), RasterReader(result[alg.P_OUTPUT_RASTER]).extent())

    def test_clipSourceGrid_by1PixelBufferedExtent(self):
        raster = QgsRasterLayer(enmap)
        extent = raster.extent().buffered(-30)

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: raster,
            alg.P_BAND_LIST: [1],
            alg.P_EXTENT: extent,
            alg.P_OUTPUT_RASTER: self.filename('enmapClipBuffered.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(extent, RasterReader(result[alg.P_OUTPUT_RASTER]).extent())

    def test_clipSourceGrid_withNonSnappedExtent(self):
        raster = QgsRasterLayer(enmap)
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: raster,
            alg.P_BAND_LIST: [1],
            alg.P_EXTENT: raster.extent().buffered(-20),
            alg.P_OUTPUT_RASTER: self.filename('enmapClipBuffered.tif')
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(raster.extent().buffered(-30), RasterReader(result[alg.P_OUTPUT_RASTER]).extent())
        self.assertEqual(raster.width() - 2, RasterReader(result[alg.P_OUTPUT_RASTER]).width())
        self.assertEqual(raster.height() - 2, RasterReader(result[alg.P_OUTPUT_RASTER]).height())

    def test_clipSourceGrid_withSourceWindow(self):
        raster = QgsRasterLayer(enmap)

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: raster,
            alg.P_BAND_LIST: [1],
        }

        # whole extent minus 1 pixel
        parameters2 = parameters.copy()
        parameters2[alg.P_SOURCE_COLUMNS] = [1, raster.width() - 2]
        parameters2[alg.P_SOURCE_ROWS] = [1, raster.height() - 2]
        parameters2[alg.P_OUTPUT_RASTER] = self.filename('enmapClipSourceWindow_buffered.tif')
        result = self.runalg(alg, parameters2)
        self.assertEqual(raster.extent().buffered(-30), RasterReader(result[alg.P_OUTPUT_RASTER]).extent())
        self.assertEqual(raster.width() - 2, RasterReader(result[alg.P_OUTPUT_RASTER]).width())
        self.assertEqual(raster.height() - 2, RasterReader(result[alg.P_OUTPUT_RASTER]).height())

        # single pixel
        parameters2 = parameters.copy()
        parameters2[alg.P_SOURCE_COLUMNS] = [50, 50]
        parameters2[alg.P_SOURCE_ROWS] = [50, 50]
        parameters2[alg.P_OUTPUT_RASTER] = self.filename('enmapClipSourceWindow_singlePixel.tif')
        result = self.runalg(alg, parameters2)
        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_RASTER]).width())
        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_RASTER]).height())
        self.assertTrue(390, RasterReader(result[alg.P_OUTPUT_RASTER]).array()[0][0, 0])

        # single row
        parameters2 = parameters.copy()
        parameters2[alg.P_SOURCE_ROWS] = [50, 50]
        parameters2[alg.P_OUTPUT_RASTER] = self.filename('enmapClipSourceWindow_singleRow.tif')
        result = self.runalg(alg, parameters2)
        self.assertEqual(raster.width(), RasterReader(result[alg.P_OUTPUT_RASTER]).width())
        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_RASTER]).height())

        # single column
        parameters2 = parameters.copy()
        parameters2[alg.P_SOURCE_COLUMNS] = [50, 50]
        parameters2[alg.P_OUTPUT_RASTER] = self.filename('enmapClipSourceWindow_singleColumn.tif')
        result = self.runalg(alg, parameters2)
        self.assertEqual(raster.height(), RasterReader(result[alg.P_OUTPUT_RASTER]).height())
        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_RASTER]).width())

    def test_resampleAlg(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_BAND_LIST: [1],
        }
        for index, name in enumerate(alg.O_RESAMPLE_ALG):
            print(name)
            parameters[alg.P_RESAMPLE_ALG] = index
            parameters[alg.P_OUTPUT_RASTER] = self.filename(f'raster.{name}.tif')
            self.runalg(alg, parameters)

    def test_copyStyle(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_COPY_STYLE: True,
            alg.P_OUTPUT_RASTER: self.filename('rasterStyled.vrt')
        }
        result = self.runalg(alg, parameters)
        layer = QgsRasterLayer(result[alg.P_OUTPUT_RASTER])
        renderer: QgsRasterRenderer = layer.renderer()
        self.assertListEqual([38, 23, 5], renderer.usesBands())

    def test_subsetBySpectralRaster(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_SPECTRAL_RASTER: hires,
            alg.P_OUTPUT_RASTER: self.filename('enmapSubsetToHires.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(3, reader.bandCount())
        self.assertListEqual([665.0, 559.0, 489.0], [reader.wavelength(i + 1) for i in range(reader.bandCount())])

    def test_scalingTo100(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_BAND_LIST: [1],
            alg.P_OFFSET: 0,
            alg.P_SCALE: 1e-4 * 100,
            alg.P_OUTPUT_RASTER: self.filename('enmapScaled.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        array = reader.array()[0]
        self.assertEqual(-1356439.5, reader.array()[0].sum())

    def test_unsetScrNoData(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_UNSET_SOURCE_NODATA: True,
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertIsNone(reader.noDataValue())

    def test_unsetDstNoData(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_UNSET_NODATA: True,
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertIsNone(reader.noDataValue())

    def test_setDstNoData(self):
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_NODATA: -123,
            alg.P_OUTPUT_RASTER: self.filename('dummy.tif')
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(-123, reader.noDataValue())

    def test_cleanEnviDomain(self):  # see issue #1098
        filename = self.filename('enmap.tif')
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_COPY_METADATA: True,
            alg.P_OUTPUT_RASTER: filename,
        }
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertIsNone(reader.metadataItem('wavelength', 'ENVI'))

    def test_writeEnviHeader(self):
        filename = self.filename('enmap.tif')
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_OUTPUT_RASTER: filename,
            alg.P_WRITE_ENVI_HEADER: True,
        }
        self.runalg(alg, parameters)
        self.assertTrue(exists(filename + '.hdr'))

    def _test_debug_issue388(self):

        # resample 30m binary byte mask into 300m fractions with AverageResampling fails because of byte output type
        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: water_mask_30m,
            alg.P_GRID: enmap_grid_300m,
            alg.P_RESAMPLE_ALG: alg.AverageResampleAlg,
            alg.P_OUTPUT_RASTER: self.filename('waterFraction1.tif'),
        }

        # use proper working type
        parameters[alg.P_WORKING_DATA_TYPE] = alg.Float32
        parameters[alg.P_OUTPUT_RASTER] = self.filename('waterFraction2.tif')
        result = self.runalg(alg, parameters)
        reader = RasterReader(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(Qgis.DataType.Float32, reader.dataType(1))
        self.assertAlmostEqual(0.52, np.max(np.unique(reader.array())))

    def _test_debug_issue888(self):

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WRITE_ENVI_HEADER: True,
            alg.P_OUTPUT_RASTER: self.filename('enmap.bsq'),
        }
        self.runalg(alg, parameters)

        with open(self.filename('enmap.hdr')) as file:
            text = file.read()
        self.assertEqual(8451, len(text))

    def _test_debug_issue1346(self):

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: enmap,
            alg.P_WRITE_ENVI_HEADER: False,
            alg.P_OUTPUT_RASTER: self.filename('copy.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        print(reader.metadata())

    def _test_debug_issue1348_case1(self):

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: r'D:\data\issues\903\PRISMA_DESTRIPPED_AOIvAL\PRISMA_DESTRIPPED_AOIvAL.bsq',
            alg.P_COPY_METADATA: True,
            alg.P_WRITE_ENVI_HEADER: True,
            alg.P_EXCLUDE_BAD_BANDS: False,
            alg.P_OUTPUT_RASTER: self.filename('case1.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        bbl = [reader.badBandMultiplier(bandNo) for bandNo in reader.bandNumbers()]
        self.assertEqual(169, sum(bbl))

    def _test_debug_issue1348_case2(self):

        alg = TranslateRasterAlgorithm()
        parameters = {
            alg.P_RASTER: r'D:\data\issues\903\PRISMA_DESTRIPPED_AOIvAL\PRISMA_DESTRIPPED_AOIvAL.bsq',
            alg.P_COPY_METADATA: True,
            alg.P_WRITE_ENVI_HEADER: True,
            alg.P_EXCLUDE_BAD_BANDS: True,
            alg.P_OUTPUT_RASTER: self.filename('case2.tif'),
        }
        self.runalg(alg, parameters)
        reader = RasterReader(parameters[alg.P_OUTPUT_RASTER])
        self.assertEqual(169, reader.bandCount())

    def _test_debug_issue501(self):

        # Given a raster with band scale factor.
        filename = r'C:\test\raster1.tif'
        driver: gdal.Driver = gdal.GetDriverByName('GTiff')
        ds: gdal.Dataset = driver.Create(filename, 10, 10, 1, gdal.GDT_Byte)
        rb = ds.GetRasterBand(1)
        rb.SetScale(0.01)
        del ds, rb

        # When translating the raster, the band scale factor is correctly assigned to the new raster.
        filename2 = r'C:\test\raster2.tif'
        gdal.Translate(filename2, filename)
        ds2: gdal.Dataset = gdal.Open(filename2)
        rb2: gdal.Band = ds2.GetRasterBand(1)
        assert rb2.GetScale() == 0.01

        # After setting a metadata item, the scale factor is still correct.
        # rb2.SetMetadataItem('myKey', '42', '')
        assert rb2.GetScale() == 0.01
        del ds2, rb2

        # But after re-opening the raster, the scale factor is missing (i.e. set to 1 -> no scaling).
        ds3 = gdal.Open(filename2)
        rb3 = ds3.GetRasterBand(1)
        assert rb3.GetScale() == 0.01  # THIS WILL FAIL
