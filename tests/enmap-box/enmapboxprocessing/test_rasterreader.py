import numpy as np
from osgeo import gdal

from enmapboxprocessing.rasterblockinfo import RasterBlockInfo
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.testcase import TestCase
from enmapboxprocessing.utils import Utils
from enmapboxtestdata import enmap, r_terra_timeseries_days, r_terra_timeseries_seconds, netCDF_timeseries_days
from enmapboxtestdata import fraction_polygon_l3
from qgis.PyQt.QtCore import QDateTime, QSizeF, QPoint
from qgis.core import QgsRasterRange, QgsRasterLayer, Qgis, QgsRectangle, QgsCoordinateReferenceSystem


class TestRasterReader(TestCase):

    def test_init(self):
        layer = QgsRasterLayer(enmap)
        reader = RasterReader(layer)
        self.assertTrue(layer is reader.layer)

        reader = RasterReader(layer.dataProvider())
        self.assertTrue(not reader.layer.isValid())

        reader = RasterReader(enmap)
        self.assertTrue(layer is not reader.layer)
        self.assertEqual(layer.source(), reader.layer.source())

        ds = gdal.Open(enmap)
        reader = RasterReader(ds)
        self.assertTrue(layer is not reader.layer)
        self.assertEqual(layer.source(), reader.layer.source())
        self.assertTrue(ds is reader.gdalDataset)

    def test_bandCount(self):
        self.assertEqual(177, RasterReader(enmap).bandCount())

    def test_bandNumbers(self):
        self.assertListEqual(list(range(1, 178)), list(RasterReader(enmap).bandNumbers()))

    def test_bandName(self):
        self.assertEqual('band 8 (0.460000 Micrometers)', RasterReader(enmap).bandName(1))

    def test_bandColor(self):
        self.assertEqual('#e60000', RasterReader(fraction_polygon_l3).bandColor(1).name())

    def test_bandOffset(self):
        self.assertEqual(0, RasterReader(enmap).bandOffset(1))

    def test_bandScale(self):
        self.assertEqual(1, RasterReader(enmap).bandScale(1))

    def test_crs(self):
        self.assertEqual('EPSG:32633', RasterReader(enmap).crs().authid())

    def test_dataType(self):
        self.assertEqual(Qgis.DataType.Int16, RasterReader(enmap).dataType())
        self.assertEqual(Qgis.DataType.Int16, RasterReader(enmap).dataType(1))

    def test_dataTypeSize(self):
        self.assertEqual(2, RasterReader(enmap).dataTypeSize())
        self.assertEqual(2, RasterReader(enmap).dataTypeSize(1))

    def test_extent(self):
        self.assertEqual(6600.0, RasterReader(enmap).extent().width())

    def test_noDataValue(self):
        self.assertEqual(-99, RasterReader(enmap).noDataValue())
        self.assertEqual(-99, RasterReader(enmap).noDataValue(1))
        self.assertEqual(-99, RasterReader(enmap).sourceNoDataValue(1))
        self.assertTrue(RasterReader(enmap).sourceHasNoDataValue(1))

        layer = QgsRasterLayer(enmap)
        reader = RasterReader(layer)
        reader.setUseSourceNoDataValue(1, False)
        self.assertEqual(False, reader.useSourceNoDataValue(1))
        self.assertEqual(False, reader.useSourceNoDataValue())

        rasterRange = QgsRasterRange(11, 111)
        reader.setUserNoDataValue(1, [rasterRange])
        self.assertListEqual([rasterRange], reader.userNoDataValues(1))
        self.assertListEqual([rasterRange], reader.userNoDataValues())

    def test_sourceHasNoDataValue(self):
        self.assertTrue(RasterReader(enmap).sourceHasNoDataValue())
        self.assertTrue(RasterReader(enmap).sourceHasNoDataValue(1))

    def test_source(self):
        self.assertEqual(enmap, RasterReader(enmap).source())

    def test_size(self):
        self.assertEqual(220, RasterReader(enmap).width())
        self.assertEqual(400, RasterReader(enmap).height())

    def test_rasterUnitsPerPixel(self):
        self.assertEqual(30.0, RasterReader(enmap).rasterUnitsPerPixelX())
        self.assertEqual(30.0, RasterReader(enmap).rasterUnitsPerPixelY())
        self.assertEqual(QSizeF(30.0, 30.0), RasterReader(enmap).rasterUnitsPerPixel())

    def test_walkGrid(self):
        lead = [rasterBlockInfo for rasterBlockInfo in RasterReader(enmap).walkGrid(200, 200)]
        gold = [
            RasterBlockInfo(
                QgsRectangle(
                    380952.36999999999534339, 5814372.34999999962747097, 386952.36999999999534339,
                    5820372.34999999962747097
                ), 0, 0, 200, 200
            ),
            RasterBlockInfo(
                QgsRectangle(
                    386952.36999999999534339, 5814372.34999999962747097, 387552.36999999999534339,
                    5820372.34999999962747097
                ), 200, 0, 20, 200
            ),
            RasterBlockInfo(
                QgsRectangle(
                    380952.36999999999534339, 5808372.34999999962747097, 386952.36999999999534339,
                    5814372.34999999962747097
                ), 0, 200, 200, 200
            ),
            RasterBlockInfo(
                QgsRectangle(
                    386952.36999999999534339, 5808372.34999999962747097, 387552.36999999999534339,
                    5814372.34999999962747097
                ), 200, 200, 20, 200
            )]
        self.assertListEqual(gold, lead)

    def test_arrayFromBlock(self):
        reader = RasterReader(enmap)
        gold = reader.gdalDataset.ReadAsArray()
        block = RasterBlockInfo(reader.extent(), 0, 0, 220, 400)
        lead = RasterReader(enmap).arrayFromBlock(block)
        self.assertTrue(np.all(np.equal(gold, lead)))

    def test_arrayFromBoundingBoxAndSize(self):
        reader = RasterReader(enmap)
        gold = reader.gdalDataset.ReadAsArray()
        lead = reader.arrayFromBoundingBoxAndSize(reader.extent(), 220, 400)
        self.assertTrue(np.all(np.equal(gold, lead)))

        lead = reader.arrayFromBoundingBoxAndSize(reader.extent(), 110, 200)
        self.assertTrue(np.all(np.equal(gold[:, 1::2, 1::2], lead)))

        lead = reader.arrayFromBoundingBoxAndSize(reader.extent(), 220, 400, [1])
        self.assertTrue(np.all(np.equal(gold[0], lead)))

        lead = reader.arrayFromBoundingBoxAndSize(reader.extent(), 220, 400, [1], 10)
        self.assertEqual((400 + 2 * 10, 220 + 2 * 10), lead[0].shape)
        self.assertTrue(np.all(np.equal(reader.noDataValue(1), lead[0][:, 0:9])))
        self.assertTrue(np.all(np.equal(gold[0], lead[0][10:-10, 10:-10])))
        lead[0][10:-10, 10:-10] = reader.noDataValue(1)
        self.assertTrue(np.all(np.equal(reader.noDataValue(1), lead)))

    def test_arrayFromPixelOffsetAndSize(self):
        array = np.zeros((1, 5, 5))
        array[0, 0] = 1
        writer = self.rasterFromArray(array)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(5, np.sum(reader.array()))
        self.assertEqual(3, np.sum(reader.array(xOffset=1, width=3)))
        self.assertEqual(0, np.sum(reader.array(yOffset=1, height=3)))

    def test_array(self):
        reader = RasterReader(enmap)
        gold = reader.gdalDataset.ReadAsArray()
        self.assertTrue(np.all(np.equal(gold, reader.array())))
        self.assertTrue(np.all(np.equal(gold, reader.array(0, 0, 220, 400))))
        self.assertTrue(np.all(np.equal(gold, reader.array(boundingBox=reader.extent()))))

    def test_array_withDataScaled(self):
        # scale only
        writer = self.rasterFromArray([[[100]]])
        writer.setScale(1e-2, 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(1, reader.array()[0][0, 0])

        # offset only
        writer = self.rasterFromArray([[[75]]])
        writer.setOffset(25, 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(100, reader.array()[0][0, 0])

        # both only
        writer = self.rasterFromArray([[[(1 - 0.5) * 100]]])
        writer.setOffset(0.5, 1)
        writer.setScale(1e-2, 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(1, reader.array()[0][0, 0])

    def test_maskArray(self):
        reader = RasterReader(enmap)
        noDataValue = reader.noDataValue(1)
        gold = reader.gdalDataset.ReadAsArray() != noDataValue
        self.assertTrue(np.all(np.equal(gold, reader.maskArray(reader.array()))))

        self.assertTrue(np.all(np.equal(True, reader.maskArray(np.array([[[42]]]), [1]))))
        self.assertTrue(np.all(np.equal(False, reader.maskArray(np.array([[[noDataValue]]]), [1]))))

        self.assertTrue(np.all(np.equal(False, reader.maskArray(np.array([[[np.nan]]]), [1], maskNotFinite=True))))
        self.assertTrue(np.all(np.equal(True, reader.maskArray(np.array([[[np.nan]]]), [1], maskNotFinite=False))))

        reader.setUseSourceNoDataValue(1, False)
        self.assertTrue(np.all(np.equal(True, reader.maskArray(np.array([[[noDataValue]]]), [1]))))

        reader = RasterReader(enmap)
        reader.setUserNoDataValue(1, [QgsRasterRange(1, 3, QgsRasterRange.BoundsType.IncludeMinAndMax)])
        self.assertTrue(np.all(np.equal(True, reader.maskArray(np.array([[[0, 4]]]), [1]))))
        self.assertTrue(np.all(np.equal(False, reader.maskArray(np.array([[[1, 2, 3]]]), [1]))))

        reader = RasterReader(enmap)
        reader.setUserNoDataValue(1, [QgsRasterRange(1, 3, QgsRasterRange.BoundsType.IncludeMin)])
        self.assertTrue(np.all(np.equal(True, reader.maskArray(np.array([[[0, 3]]]), [1]))))
        self.assertTrue(np.all(np.equal(False, reader.maskArray(np.array([[[1, 2]]]), [1]))))

        reader = RasterReader(enmap)
        reader.setUserNoDataValue(1, [QgsRasterRange(1, 3, QgsRasterRange.BoundsType.IncludeMax)])
        self.assertTrue(np.all(np.equal(True, reader.maskArray(np.array([[[1, 4]]]), [1]))))
        self.assertTrue(np.all(np.equal(False, reader.maskArray(np.array([[[2, 3]]]), [1]))))

        reader = RasterReader(enmap)
        reader.setUserNoDataValue(1, [QgsRasterRange(1, 3, QgsRasterRange.BoundsType.Exclusive)])
        self.assertTrue(np.all(np.equal(True, reader.maskArray(np.array([[[1, 3]]]), [1]))))
        self.assertTrue(np.all(np.equal(False, reader.maskArray(np.array([[[2]]]), [1]))))

    def test_maskArray_withDefaultNoDataValue(self):
        writer = self.rasterFromArray([[[1]]])
        writer.close()
        reader = RasterReader(writer.source())
        self.assertTrue(np.all(reader.maskArray(np.array([[[1]]]))))
        self.assertTrue(np.all(~reader.maskArray(np.array([[[1]]]), defaultNoDataValue=1)[0]))

    def test_samplingWidthAndHeight(self):
        reader = RasterReader(enmap)
        self.assertEqual((220, 400), reader.samplingWidthAndHeight(1))
        self.assertEqual((220, 400), reader.samplingWidthAndHeight(1, reader.extent()))
        extent = QgsRectangle(380952.37, 5808372.35, 380952.37 + 30, 5808372.35 + 30)  # single pixel
        self.assertEqual((1, 1), reader.samplingWidthAndHeight(1, extent))
        self.assertEqual((8, 14), reader.samplingWidthAndHeight(1, reader.extent(), 100))

    def test_samplingWidthAndHeight_singlePixel(self):
        reader = RasterReader(enmap)
        extent = reader.pixelExtent(QPoint(42, 42))
        self.assertEqual((1, 1), reader.samplingWidthAndHeight(1, extent))

    def test_sampleValues(self):
        reader = RasterReader(enmap)
        array = reader.array(bandList=[1])[0]
        noDataValue = reader.noDataValue(1)
        self.assertEqual(np.sum(array != noDataValue), reader.sampleValues(1).shape)
        self.assertEqual(np.sum(array[array != noDataValue]), np.sum(reader.sampleValues(1)))
        self.assertEqual(400 * 220, len(reader.sampleValues(1, excludeNoDataValues=False)))

    def test_uniqueValueCounts(self):
        writer = self.rasterFromArray([[[1, 1, 1, 2, 2, 3]]])
        writer.close()
        reader = RasterReader(writer.source())
        uniqueValues, counts = reader.uniqueValueCounts(1)
        self.assertListEqual(uniqueValues, [1, 2, 3])
        self.assertListEqual(counts, [3, 2, 1])

    def test_metadataItem(self):
        reader = RasterReader(enmap)
        self.assertEqual('0.460000', reader.metadataItem('wavelength', 'ENVI')[0])
        self.assertEqual('Micrometers', reader.metadataItem('wavelength units', 'ENVI'))
        self.assertEqual('0.460000', reader.metadataItem('wavelength', '', 1))

    def test_metadataDomain(self):
        reader = RasterReader(enmap)
        # self.assertEqual(20, len(reader.metadataDomain('ENVI')))

    def test_metadata(self):
        reader = RasterReader(enmap)

    def test_metadataDomainKeys(self):
        reader = RasterReader(enmap)
        self.assertEqual(4, len(reader.metadata()))

    def test_isSpectralRasterLayer(self):
        reader = RasterReader(enmap)
        self.assertTrue(reader.isSpectralRasterLayer())
        self.assertTrue(reader.isSpectralRasterLayer(False))

        reader = RasterReader(fraction_polygon_l3)
        self.assertFalse(reader.isSpectralRasterLayer())
        self.assertFalse(reader.isSpectralRasterLayer(False))

    def test_findBandName(self):
        reader = RasterReader(enmap)
        bandName = reader.bandName(42)
        self.assertEqual(42, reader.findBandName(bandName))
        self.assertIsNone(reader.findBandName('dummy'))

    def test_wavelengthUnits(self):
        # check at band-level
        writer = self.rasterFromArray(np.zeros((4, 1, 1)))
        writer.setMetadataItem('wavelength', 500, '', 1)
        writer.setMetadataItem('wavelength', 0.5, '', 2)
        writer.setMetadataItem('wavelength', 1000, '', 3)
        writer.setMetadataItem('wavelength', 1000, '', 4)
        writer.setMetadataItem('wavelength_units', 'Nanometers', '', 3)
        writer.setMetadataItem('wavelength_unit', 'Micrometers', '', 4)
        writer.close(stac=True)
        reader = RasterReader(writer.source())
        self.assertEqual('Micrometers', reader.wavelengthUnits(1))  # STAC stores it as Micrometers
        self.assertEqual('Micrometers', reader.wavelengthUnits(2))  # STAC stores it as Micrometers
        self.assertEqual('Micrometers', reader.wavelengthUnits(3))  # STAC stores it as Micrometers
        self.assertEqual('Micrometers', reader.wavelengthUnits(4))  # STAC stores it as Micrometers

        # check at dataset-level
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('wavelength_units', 'Nanometers', '')
        writer.close()

    def test_wavelength(self):
        # check at band-level (no units)
        writer = self.rasterFromArray(np.zeros((5, 1, 1)))
        writer.setMetadataItem('wavelength', 1, '', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(1, reader.wavelength(1, raw=True))  # raw
        self.assertEqual(1000, reader.wavelength(1))  # in Nanometers
        self.assertEqual(1, reader.wavelength(1, 'Micrometers'))

        # check at band-level (with units)
        writer = self.rasterFromArray(np.zeros((5, 1, 1)))
        writer.setMetadataItem('wavelength', 0.5, '', 1)
        writer.setMetadataItem('wavelength_units', 'Micrometers', '', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(500, reader.wavelength(1))  # in Nanometers
        self.assertEqual(0.5, reader.wavelength(1, 'Micrometers'))

        # check at dataset-level
        writer = self.rasterFromArray(np.zeros((2, 1, 1)))
        writer.setMetadataItem('wavelength', [0.5, 500], '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(500, reader.wavelength(1))
        self.assertEqual(500, reader.wavelength(2))

    def test_wavelengthFromGdalImageryDomain(self):

        writer = self.rasterFromArray(np.zeros((1, 1, 1)))
        writer.setMetadataItem('CENTRAL_WAVELENGTH_UM', 42, 'IMAGERY', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual('Micrometers', reader.wavelengthUnits(1))
        self.assertEqual(42 * 1000, reader.wavelength(1))

    def test_findWavelength(self):
        writer = self.rasterFromArray(np.zeros((5, 1, 1)))
        writer.setWavelength(100, 1)
        writer.setWavelength(200, 2)
        writer.setWavelength(300, 3)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(2, reader.findWavelength(190))
        self.assertEqual(2, reader.findWavelength(190, reader.Nanometers))
        self.assertIsNone(reader.findWavelength(None))

    def test_findWavelength_nonSpectralRaster(self):
        writer = self.rasterFromArray(np.zeros((5, 1, 1)))
        writer.close()
        reader = RasterReader(writer.source())
        self.assertIsNone(reader.findWavelength(190))

    def test_fwhm(self):
        reader = RasterReader(enmap)

        if reader.fwhm(1) == 6.0:
            return  # skip test because of a value-rounding bug in GDAL

        self.assertEqual(5.8, reader.fwhm(1))  # in Nanometers

        # check at band-level
        writer = self.rasterFromArray(np.zeros((1, 1, 1)))
        writer.setMetadataItem('wavelength_units', 'Nanometers', '', 1)
        writer.setMetadataItem('fwhm', 10, '', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(10, reader.fwhm(1))  # in Nanometers
        self.assertEqual(0.01, reader.fwhm(1, 'Micrometers'))

        # check at dataset-level
        writer = self.rasterFromArray(np.zeros((2, 1, 1)))
        writer.setMetadataItem('fwhm', [10, 20], '')
        writer.setMetadataItem('wavelength_units', 'Nanometers', '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(10, reader.fwhm(1))
        self.assertEqual(20, reader.fwhm(2))

        # check non-spectral raster
        self.assertIsNone(RasterReader(fraction_polygon_l3).fwhm(1))

    def test_badBandMultiplier(self):
        # check at band-level
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('bbl', 0, '', 1)
        writer.setMetadataItem('bbl', 1, '', 2)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(0, reader.badBandMultiplier(1))
        self.assertEqual(1, reader.badBandMultiplier(2))
        self.assertEqual(1, reader.badBandMultiplier(3))

        # check at dataset-level
        writer = self.rasterFromArray(np.zeros((2, 1, 1)))
        writer.setMetadataItem('bbl', [0, 1], '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(0, reader.badBandMultiplier(1))
        self.assertEqual(1, reader.badBandMultiplier(2))

    def test_startTime(self):
        # no time set
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.close()
        reader = RasterReader(writer.source())
        self.assertIsNone(reader.startTime())
        self.assertIsNone(reader.startTime(1))

        # check at dataset-level
        # - standard format
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('start_time', '2009-08-20T09:44:50', '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime(1))
        # - GDAL IMAGERY-domain
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('ACQUISITIONDATETIME', '2009-08-20T09:44:50', 'IMAGERY')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime(1))
        # - ENVI-domain
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('acquisition_time', '2009-08-20T09:44:50', 'ENVI')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime(1))

        # check at dataset-level
        # - standard format
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('start_time', '2009-08-20T09:44:50', '', 1)
        writer.setMetadataItem('Date', '2009-08-20T09:44:50', 'FORCE', 2)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime(1))
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime(2))

    def test_terra_timeseries(self):
        # .aux.json files created with R-cran terra package
        reader = RasterReader(r_terra_timeseries_days)
        self.assertEqual(QDateTime(2015, 7, 4, 0, 0, 0), reader.startTime(1))
        reader = RasterReader(r_terra_timeseries_seconds)
        self.assertEqual(QDateTime(2015, 7, 4, 9, 7, 2), reader.startTime(1))

    def test_netCDF_timeseries(self):
        # NETCDF_DIM_time
        reader = RasterReader(netCDF_timeseries_days)
        self.assertEqual(QDateTime(2015, 7, 4, 0, 0, 0), reader.startTime(1))

    def test_startTime_bandLevel(self):
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('start_time', '2009-08-20T09:44:50', '', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.startTime(1))

    def test_endTime1(self):
        # no time set
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.close()
        reader = RasterReader(writer.source())
        self.assertIsNone(reader.endTime())
        self.assertIsNone(reader.endTime(1))

    def test_endTime2(self):
        # check at dataset-level
        # - standard format
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('end_time', '2009-08-20T09:44:50', '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.endTime(1))

    def test_endTime3(self):
        # check at band-level
        # - standard format
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('end_time', '2009-08-20T09:44:50', '', 1)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.endTime(1))

    def test_centerTime(self):
        # no start time set
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.close()
        reader = RasterReader(writer.source())
        self.assertIsNone(reader.centerTime())
        self.assertIsNone(reader.centerTime(1))

        # no end time, but start time set
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('start_time', '2009-08-20T09:44:50', '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.centerTime())
        self.assertEqual(QDateTime(2009, 8, 20, 9, 44, 50), reader.centerTime(1))

        # check both set
        # - standard format
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.setMetadataItem('start_time', '2009-08-20T09:44:50', '')
        writer.setMetadataItem('end_time', '2011-08-20T09:44:50', '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2010, 8, 20, 9, 44, 50), reader.centerTime(1))

    def test_centerTime_ForceTSIFormat_v1_2(self):  # see #111
        writer = self.rasterFromArray(np.zeros((1, 1, 1)))
        writer.setMetadataItem('wavelength', 2015.003, '', 1)
        writer.setMetadataItem('description', '{FORCE v. 1.2_beta Time Series Analysis}', 'ENVI')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertIsNone(reader.wavelength(1))
        self.assertEqual(Utils.decimalYearToDateTime(2015.003), reader.centerTime(1))
        self.assertIsNone(reader.wavelengthUnits(1))

    def test_centerTime_NETCDF_DIM_time_format(self):  # see #251
        writer = self.rasterFromArray(np.zeros((1, 1, 1)))
        writer.setMetadataItem('NETCDF_DIM_time ', 1, '', 1)
        writer.setMetadataItem('time#units', 'days since 1970-1-1', '')
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(1970, 1, 2, 0, 0), reader.centerTime(1))

    def test_findTime(self):
        writer = self.rasterFromArray(np.zeros((4, 1, 1)))
        writer.setStartTime(QDateTime(2000, 1, 1, 0, 0), 1)
        writer.setStartTime(QDateTime(2010, 1, 1, 0, 0), 2)
        writer.setStartTime(QDateTime(2020, 1, 1, 0, 0), 3)
        writer.close()
        reader = RasterReader(writer.source())
        self.assertEqual(2, reader.findTime(QDateTime(2009, 1, 1, 0, 0)))

        self.assertIsNone(reader.findTime(None))

        # non-temporal raster
        writer = self.rasterFromArray(np.zeros((3, 1, 1)))
        writer.close()
        reader = RasterReader(writer.source())
        self.assertIsNone(reader.findTime(QDateTime(2009, 1, 1, 0, 0)))

    def test_lineMemoryUsage(self):
        bandCount = 4
        xsize = 10
        dataTypeSize = 4  # np.int32 uses 4 bytes
        writer = self.rasterFromArray(np.zeros((bandCount, 1, xsize), np.int32))
        writer.close()
        reader = RasterReader(writer.source())
        gold = bandCount * xsize * dataTypeSize
        self.assertEqual(gold, reader.lineMemoryUsage())
        self.assertEqual(gold * 2, reader.lineMemoryUsage(nBands=bandCount * 2))
        self.assertEqual(gold * 2, reader.lineMemoryUsage(dataTypeSize=8))

    def test_stacMetadata(self):
        writer = self.rasterFromArray(np.zeros((1, 5, 5)), 'raster.tif')
        writer.close()
        stacMetadata = {
            "properties": {
                "dataset_key": 42,
                "eo:bands": [
                    {
                        "name": "A",
                        "center_wavelength": 1,
                        "full_width_half_max": 0.1,
                        "datetime": "2022-01-01T12:00:00",
                        "enmapbox:bad_band_multiplier": 0,
                        "band_key": 42,
                    }
                ]
            }
        }
        Utils().jsonDump(stacMetadata, writer.source() + '.stac.json')

        reader = RasterReader(writer.source())
        self.assertEqual(42, reader.metadataItem('dataset_key'))
        self.assertEqual(42, reader.metadataItem('band_key', '', 1))
        self.assertEqual('A', reader.bandName(1))
        self.assertEqual(reader.Micrometers, reader.wavelengthUnits(1))
        self.assertEqual(1000, reader.wavelength(1))
        self.assertEqual(100, reader.fwhm(1))
        self.assertEqual(QDateTime(2022, 1, 1, 12, 0, 0), reader.startTime(1))
        self.assertIsNone(reader.endTime(1))
        self.assertEqual(QDateTime(2022, 1, 1, 12, 0, 0), reader.centerTime(1))
        self.assertEqual(0, reader.badBandMultiplier(1))

    def test_stacMetadata_dateTimeRange(self):
        writer = self.rasterFromArray(np.zeros((1, 5, 5)), 'raster.tif')
        stacMetadata = {
            "properties": {
                "eo:bands": [
                    {
                        "start_datetime": "2022-01-01T12:00:00",
                        "end_datetime": "2022-01-03T12:00:00",
                    }
                ]
            }
        }
        Utils().jsonDump(stacMetadata, writer.source() + '.stac.json')
        writer.close()

        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2022, 1, 1, 12, 0, 0), reader.startTime(1))
        self.assertEqual(QDateTime(2022, 1, 3, 12, 0, 0), reader.endTime(1))
        self.assertEqual(QDateTime(2022, 1, 2, 12, 0, 0), reader.centerTime(1))

    def test_stacMetadata_enviStyle(self):
        writer = self.rasterFromArray(np.zeros((2, 5, 5)), 'raster.tif')
        writer.close()
        stacMetadata = {
            "properties": {
                "envi:metadata": {
                    "band_names": ["Band A", "Band B"],
                    "wavelength": [1, 2],
                    "wavelength_units": "Micrometers",
                    "fwhm": [0.1, 0.2],
                    "bbl": [1, 0],
                    "acquisition_time": "2022-01-01T12:00:00",
                    "my_key": 42
                }
            }
        }
        Utils().jsonDump(stacMetadata, writer.source() + '.stac.json')

        reader = RasterReader(writer.source())
        self.assertEqual('Band A', reader.bandName(1))
        self.assertEqual('Band B', reader.bandName(2))
        self.assertEqual(reader.Micrometers, reader.wavelengthUnits(1))
        self.assertEqual(reader.Micrometers, reader.wavelengthUnits(2))
        self.assertEqual(1000, reader.wavelength(1))
        self.assertEqual(2000, reader.wavelength(2))
        self.assertEqual(100, reader.fwhm(1))
        self.assertEqual(200, reader.fwhm(2))
        self.assertEqual(1, reader.badBandMultiplier(1))
        self.assertEqual(0, reader.badBandMultiplier(2))
        self.assertEqual(QDateTime(2022, 1, 1, 12, 0, 0), reader.startTime())
        self.assertIsNone(reader.endTime(1))
        self.assertEqual(QDateTime(2022, 1, 1, 12, 0, 0), reader.centerTime())
        self.assertEqual(42, reader.metadataItem('my_key', 'envi'))

    def test_stacMetadata_enviStyle_datetime(self):
        writer = self.rasterFromArray(np.zeros((2, 5, 5)), 'raster.tif')
        stacMetadata = {
            "properties": {
                "envi:metadata": {
                    "eo:datetime": ["2022-01-01T12:00:00", "2023-01-01T12:00:00"]
                }
            }
        }
        Utils().jsonDump(stacMetadata, writer.source() + '.stac.json')
        writer.close()

        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2022, 1, 1, 12, 0, 0), reader.startTime(1))
        self.assertEqual(QDateTime(2022, 1, 1, 12, 0, 0), reader.centerTime(1))
        self.assertEqual(QDateTime(2023, 1, 1, 12, 0, 0), reader.startTime(2))
        self.assertEqual(QDateTime(2023, 1, 1, 12, 0, 0), reader.centerTime(2))

    def test_stacMetadata_enviStyle_datetime2(self):
        writer = self.rasterFromArray(np.zeros((2, 5, 5)), 'raster.tif')
        stacMetadata = {
            "properties": {
                "envi:metadata": {
                    "eo:start_datetime": ["2022-01-01T00:00:00", "2023-01-01T00:00:00"],
                    "eo:end_datetime": ["2023-01-01T00:00:00", "2024-01-01T00:00:00"]
                }
            }
        }
        Utils().jsonDump(stacMetadata, writer.source() + '.stac.json')
        writer.close()

        reader = RasterReader(writer.source())
        self.assertEqual(QDateTime(2022, 1, 1, 0, 0, 0), reader.startTime(1))
        self.assertEqual(QDateTime(2023, 1, 1, 0, 0, 0), reader.endTime(1))
        self.assertEqual(QDateTime(2023, 1, 1, 0, 0, 0), reader.startTime(2))
        self.assertEqual(QDateTime(2024, 1, 1, 0, 0, 0), reader.endTime(2))

    def test_nonGdalSource(self):
        layer = QgsRasterLayer(
            r'type=xyz&url=https://mt1.google.com/vt/lyrs%3Dm%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0',
            'Google Maps', 'wms'
        )
        reader = RasterReader(layer, openWithGdal=False)
        self.assertEqual(1, reader.bandCount())

        self.assertEqual(1, reader.badBandMultiplier(1))
        self.assertIsNone(reader.bandColor(1))
        self.assertEqual('', reader.bandName(1))
        self.assertEqual(0, reader.bandOffset(1))
        self.assertEqual(1, reader.bandScale(1))
        self.assertIsNone(reader.centerTime(1))
        self.assertEqual(Qgis.DataType.ARGB32, reader.dataType(1))
        self.assertEqual(4, reader.dataTypeSize(1))
        self.assertIsNone(reader.endTime(1))
        self.assertIsNone(reader.fwhm(1))
        self.assertFalse(reader.isSpectralRasterLayer())
        self.assertIsNone(reader.wavelength(1))
        self.assertIsNone(reader.wavelengthUnits(1))

    def test_arrayFromBoundingBoxAndSize_withRasterPipe(self):
        reader = RasterReader(enmap, True, QgsCoordinateReferenceSystem('EPSG:4326'))
        extent4326 = QgsRectangle(
            13.24539916899924741, 52.41274014201967901, 13.34677689752254182, 52.52184188795427389
        )
        array = reader.arrayFromBoundingBoxAndSize(extent4326, 10, 10, [1])
        print(array)

        # self.assertTrue(np.all(np.equal(reader.noDataValue(1), lead)))
