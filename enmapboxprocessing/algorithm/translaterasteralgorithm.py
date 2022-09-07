from math import isnan
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.writeenviheaderalgorithm import WriteEnviHeaderAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRectangle, QgsRasterLayer,
                       QgsRasterDataProvider, QgsPoint, QgsPointXY, QgsMapLayer)
from typeguard import typechecked


@typechecked
class TranslateRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_BAND_LIST, _BAND_LIST = 'bandList', 'Selected bands'
    P_GRID, _GRID = 'grid', 'Grid'
    P_SPECTRAL_RASTER, _SPECTRAL_RASTER = 'spectralSubset', 'Spectral raster layer for band subsetting'
    P_SPECTRAL_BAND_LIST, _SPECTRAL_BAND_LIST = 'spectralBandList', 'Selected spectral bands'
    P_OFFSET, _OFFSET = 'offset', 'Data offset value'
    P_SCALE, _SCALE = 'scale', 'Data gain/scale value'
    P_COPY_METADATA, _COPY_METADATA = 'copyMetadata', 'Copy metadata'
    P_COPY_STYLE, _COPY_STYLE = 'copyStyle', 'Copy style'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS = 'excludeBadBands', 'Exclude bad bands'
    P_WRITE_ENVI_HEADER, _WRITE_ENVI_HEADER = 'writeEnviHeader', 'Write ENVI header'
    P_EXTENT, _EXTENT = 'extent', 'Spatial extent'
    P_SOURCE_COLUMNS, _SOURCE_COLUMNS = 'sourceColumns', 'Column subset'
    P_SOURCE_ROWS, _SOURCE_ROWS = 'sourceRows', 'Row subset'
    P_RESAMPLE_ALG, _RESAMPLE_ALG = 'resampleAlg', 'Resample algorithm'
    P_SOURCE_NODATA, _SOURCE_NODATA = 'sourceNoData', 'Source no data value'
    P_NODATA, _NODATA = 'noData', 'No data value'
    P_UNSET_SOURCE_NODATA, _UNSET_SOURCE_NODATA = 'unsetSourceNoData', 'Unset source no data value'
    P_UNSET_NODATA, _UNSET_NODATA = 'unsetNoData', 'Unset no data value'
    P_WORKING_DATA_TYPE, _WORKING_DATA_TYPE = 'workingType', 'Working Data type'
    P_DATA_TYPE, _DATA_TYPE = 'dataType', 'Data type'
    P_CREATION_PROFILE, _CREATION_PROFILE = 'creationProfile', 'Output options'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputTranslatedRaster', 'Output raster layer'

    def displayName(self):
        return 'Translate raster layer'

    def shortDescription(self):
        return 'Convert raster data between different formats, ' \
               'potentially performing some operations like spatial subsetting, spatial resampling, reprojection, ' \
               'band subsetting, band reordering, data scaling, no data value specification, and data type conversion.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Source raster layer.'),
            (self._BAND_LIST, 'Bands to subset and rearrange. '
                              'An empty selection defaults to all bands in native order.'),
            (self._GRID, 'The destination grid.'),
            (self._COPY_METADATA, 'Whether to copy GDAL metadata from source to destination.'),
            (self._COPY_STYLE, 'Whether to copy style from source to destination.'),
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bad bands (given by BBL metadata item inside ENVI domain). '
                                      'Also see The ENVI Header Format for more details: '
                                      'https://www.l3harrisgeospatial.com/docs/ENVIHeaderFiles.html '),
            (self._WRITE_ENVI_HEADER, 'Whether to write an ENVI header *.hdr sidecar file with '
                                      'spectral metadata required for proper visualization in ENVI software.'),
            (self._CREATION_PROFILE, 'Output format and creation options. '
                                     'The default format is GeoTiff with creation options: '
                                     '' + ', '.join(self.DefaultGTiffCreationOptions)),
            (self._SPECTRAL_RASTER, 'A spectral raster layer used for specifying a band subset '
                                    'by matching the center wavelength.'),
            (self._SPECTRAL_BAND_LIST, 'Spectral bands used to match source raster bands.'
                                       'An empty selection defaults to all bands in native order.'),
            (self._OFFSET, 'A data offset value applied to each band.'),
            (self._SCALE, 'A data gain/scale value applied to each band.'),
            (self._EXTENT, 'Spatial extent for clipping the destination grid, '
                           'which is given by the source Raster or the selected Grid. '
                           'In both cases, the extent is aligned with the actual pixel grid '
                           'to avoid subpixel shifts.'),
            (self._SOURCE_COLUMNS, 'Column subset range in pixels to extract.'),
            (self._SOURCE_ROWS, 'Rows subset range in pixels to extract.'),
            (self._RESAMPLE_ALG, 'Spatial resample algorithm.'),
            (self._SOURCE_NODATA, 'The value to be used instead of the original raster layer no data value.'),
            (self._NODATA, 'The value to be used instead of the default destination no data value.'),
            (self._UNSET_SOURCE_NODATA, 'Whether to unset (i.e. not use) the source no data value.'),
            (self._UNSET_NODATA, 'Whether to unset the destination no data value.'),
            (self._WORKING_DATA_TYPE, 'Working data type that is applied before resampling.'),
            (self._DATA_TYPE, 'Output data type.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        return True, ''

    def parameterAsSourceWindowExtent(
            self, parameters: Dict[str, Any], context: QgsProcessingContext
    ) -> QgsRectangle:

        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        provider: QgsRasterDataProvider = raster.dataProvider()

        xmin, xmax = self.parameterAsRange(parameters, self.P_SOURCE_COLUMNS, context)
        ymin, ymax = self.parameterAsRange(parameters, self.P_SOURCE_ROWS, context)
        skipRangeX = isnan(xmin) and isnan(xmax)
        skipRangeY = isnan(ymin) and isnan(ymax)
        if skipRangeX and skipRangeY:
            return QgsRectangle()

        if isnan(xmin):
            xmin = 0
        if isnan(ymin):
            ymin = 0
        if isnan(xmax):
            xmax = xmin + raster.width() - 1
        if isnan(ymax):
            ymax = ymin + raster.height() - 1
        p1: QgsPoint = provider.transformCoordinates(QgsPoint(xmin, ymin), QgsRasterDataProvider.TransformImageToLayer)
        p2: QgsPoint = provider.transformCoordinates(
            QgsPoint(xmax + 1, ymax + 1), QgsRasterDataProvider.TransformImageToLayer
        )
        return QgsRectangle(QgsPointXY(p1), QgsPointXY(p2))

    def group(self):
        return Group.Test.value + Group.RasterConversion.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBandList(
            self.P_BAND_LIST, self._BAND_LIST, parentLayerParameterName=self.P_RASTER, optional=True
        )
        self.addParameterRasterLayer(self.P_GRID, self._GRID, optional=True)
        self.addParameterBoolean(self.P_COPY_METADATA, self._COPY_METADATA, defaultValue=False)
        self.addParameterBoolean(self.P_COPY_STYLE, self._COPY_STYLE, defaultValue=False)
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, defaultValue=False)
        self.addParameterBoolean(self.P_WRITE_ENVI_HEADER, self._WRITE_ENVI_HEADER, defaultValue=True)
        self.addParameterRasterLayer(self.P_SPECTRAL_RASTER, self._SPECTRAL_RASTER, None, True, True)
        self.addParameterBandList(
            self.P_SPECTRAL_BAND_LIST, self._SPECTRAL_BAND_LIST, None, self.P_SPECTRAL_RASTER, True, True
        )
        self.addParameterFloat(self.P_OFFSET, self._OFFSET, None, True, None, None, True)
        self.addParameterFloat(self.P_SCALE, self._SCALE, None, True, None, None, True)
        self.addParameterExtent(self.P_EXTENT, self._EXTENT, optional=True, advanced=True)
        self.addParameterIntRange(self.P_SOURCE_COLUMNS, self._SOURCE_COLUMNS, optional=True, advanced=True)
        self.addParameterIntRange(self.P_SOURCE_ROWS, self._SOURCE_ROWS, optional=True, advanced=True)
        self.addParameterResampleAlg(self.P_RESAMPLE_ALG, self._RESAMPLE_ALG, advanced=True)
        self.addParameterFloat(self.P_SOURCE_NODATA, self._SOURCE_NODATA, None, True, None, None, True)
        self.addParameterFloat(self.P_NODATA, self._NODATA, None, True, None, None, True)
        self.addParameterBoolean(self.P_UNSET_SOURCE_NODATA, self._UNSET_SOURCE_NODATA, False, False, True)
        self.addParameterBoolean(self.P_UNSET_NODATA, self._UNSET_NODATA, False, False, True)
        self.addParameterDataType(self.P_WORKING_DATA_TYPE, self._WORKING_DATA_TYPE, None, True, True)
        self.addParameterDataType(self.P_DATA_TYPE, self._DATA_TYPE, optional=True, advanced=True)
        self.addParameterCreationProfile(self.P_CREATION_PROFILE, self._CREATION_PROFILE, '', True, False)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER, allowEnvi=True, allowVrt=True)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        provider: QgsRasterDataProvider = raster.dataProvider()
        bandList = self.parameterAsInts(parameters, self.P_BAND_LIST, context)
        grid = self.parameterAsRasterLayer(parameters, self.P_GRID, context)
        if grid is None:
            grid = raster
        spectralRaster = self.parameterAsSpectralRasterLayer(parameters, self.P_SPECTRAL_RASTER, context)
        spectralBandList = self.parameterAsInts(parameters, self.P_SPECTRAL_BAND_LIST, context)
        offset = self.parameterAsFloat(parameters, self.P_OFFSET, context)
        scale = self.parameterAsFloat(parameters, self.P_SCALE, context)
        extent = self.parameterAsExtent(parameters, self.P_EXTENT, context, crs=grid.crs())
        if not extent.isEmpty():
            extent = Utils.snapExtentToRaster(extent, grid)
        sourceWindowExtent = self.parameterAsSourceWindowExtent(parameters, context)
        if not sourceWindowExtent.isEmpty():
            extent = sourceWindowExtent
            grid = raster  # even if grid is specified, use the source raster
        if extent.isEmpty():
            extent = grid.extent()
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
        resampleAlg = self.parameterAsGdalResampleAlg(parameters, self.P_RESAMPLE_ALG, context)
        srcNoDataValue = self.parameterAsFloat(parameters, self.P_SOURCE_NODATA, context)
        dstNoDataValue = self.parameterAsFloat(parameters, self.P_NODATA, context)
        unsetSrcNoDataValue = self.parameterAsBoolean(parameters, self.P_UNSET_SOURCE_NODATA, context)
        unsetDstNoDataValue = self.parameterAsBoolean(parameters, self.P_UNSET_NODATA, context)
        dataType = self.parameterAsQgsDataType(parameters, self.P_DATA_TYPE, context, default=provider.dataType(1))
        workingDataType = self.parameterAsQgsDataType(parameters, self.P_WORKING_DATA_TYPE, context)
        copyMetadata = self.parameterAsBoolean(parameters, self.P_COPY_METADATA, context)
        copyStyle = self.parameterAsBoolean(parameters, self.P_COPY_STYLE, context)
        writeEnviHeader = self.parameterAsBoolean(parameters, self.P_WRITE_ENVI_HEADER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        format, options = self.parameterAsCreationProfile(parameters, self.P_CREATION_PROFILE, context, filename)
        width = int(round(extent.width() / grid.rasterUnitsPerPixelX()))
        height = int(round(extent.height() / grid.rasterUnitsPerPixelY()))
        crs = grid.crs()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)
            gdalDataType = Utils.qgisDataTypeToGdalDataType(dataType)

            # bad bands subset
            if excludeBadBands:
                if bandList is None:
                    bandList = [bandNo for bandNo in range(1, reader.bandCount() + 1)
                                if reader.badBandMultiplier(bandNo) == 1]
                else:
                    bandList = [bandNo for bandNo in bandList
                                if reader.badBandMultiplier(bandNo) == 1]

            # spectral subset
            if spectralRaster is not None:
                spectralReader = RasterReader(spectralRaster)

                if bandList is None:
                    bandList = [i + 1 for i in range(reader.bandCount())]

                if spectralBandList is None:
                    spectralBandList = [i + 1 for i in range(spectralRaster.bandCount())]

                wavelength = np.array([reader.wavelength(bandNo) for bandNo in bandList])
                bandList = [int(np.argmin(np.abs(wavelength - spectralReader.wavelength(bandNo))) + 1)
                            for bandNo in spectralBandList]

            if bandList is None:
                nBands = raster.bandCount()
            else:
                nBands = len(bandList)

            # derive source and destination no data values
            if srcNoDataValue is None:
                # get no data value from QGIS layer and layer properties
                if reader.sourceHasNoDataValue() and reader.useSourceNoDataValue():
                    srcNoDataValue = None  # use default no data value
                else:
                    rasterRanges = reader.userNoDataValues()
                    if len(rasterRanges) == 1:
                        srcNoDataValue = rasterRanges[0].min()  # use user no data value
                    else:
                        srcNoDataValue = 'none'  # unset no data value
            if unsetSrcNoDataValue:
                srcNoDataValue = 'none'  # unset no data value
            if unsetDstNoDataValue:
                dstNoDataValue = 'none'  # unset no data value

            infoTail = f' [{width}x{height}x{nBands}]({Utils.qgisDataTypeName(dataType)})'
            if format is not None:
                infoTail += f' -of {format}'
            if options is not None:
                infoTail += f' -co {" ".join(options)}'
            infoTail += f' {filename}'

            if workingDataType is None:
                rasterSource = raster.source()
            else:
                rasterSource = Utils.tmpFilename(filename, 'workingRaster.tif')
                gdal.Translate(
                    rasterSource, raster.source(),
                    options=gdal.TranslateOptions(outputType=Utils.qgisDataTypeToGdalDataType(workingDataType))
                )

            gdalDataset = gdal.Open(rasterSource)
            assert gdalDataset is not None

            callback = Utils.qgisFeedbackToGdalCallback(feedback)
            resampleAlgSupportedByGdalTranslate = resampleAlg not in [gdal.GRA_Min, gdal.GRA_Q1, gdal.GRA_Med,
                                                                      gdal.GRA_Q3, gdal.GRA_Max]
            useGdalTranslate = raster.crs() == crs and resampleAlgSupportedByGdalTranslate and dstNoDataValue is None
            if useGdalTranslate:
                feedback.pushInfo('Translate raster' + infoTail)

                projWin = (extent.xMinimum(), extent.yMaximum(), extent.xMaximum(), extent.yMinimum())
                if not grid.crs().isValid():
                    # dirty fix for issue #1082
                    if abs(projWin[2]) == raster.width() and abs(projWin[3]) == raster.height():
                        projWin = None

                translateOptions = gdal.TranslateOptions(
                    format=format, width=width, height=height, creationOptions=options, resampleAlg=resampleAlg,
                    projWin=projWin, bandList=bandList, outputType=gdalDataType, callback=callback,
                    noData=srcNoDataValue
                )
                outGdalDataset: gdal.Dataset = gdal.Translate(
                    destName=filename, srcDS=gdalDataset, options=translateOptions
                )
                assert outGdalDataset is not None

                # need to explicitely set the GeoTransform tuple, because gdal.Translate extent may deviate slightly
                if grid.crs().isValid():
                    ulx, uly, lrx, lry = projWin
                    xres = (lrx - ulx) / width
                    yres = (uly - lry) / height
                    geoTransform = (ulx, xres, 0., uly, 0., -yres)
                    outGdalDataset.SetGeoTransform(geoTransform)
            else:  # use gdal warp
                if bandList is not None:
                    tmpFilename = Utils.tmpFilename(filename, 'bandSubset.vrt')
                    tmpGdalDataset = gdal.Translate(
                        destName=tmpFilename, srcDS=gdalDataset, format=self.VrtFormat, bandList=bandList,
                        noData=srcNoDataValue, callback=callback
                    )
                else:
                    tmpGdalDataset = gdalDataset

                feedback.pushInfo('Warp raster' + infoTail)
                outputBounds = (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())
                dstSRS = crs.toWkt()
                resampleAlgString = Utils.gdalResampleAlgToGdalWarpFormat(resampleAlg)
                warpOptions = gdal.WarpOptions(
                    format=format, width=width, height=height, creationOptions=options, resampleAlg=resampleAlgString,
                    outputBounds=outputBounds, outputType=gdalDataType, dstSRS=dstSRS, srcNodata=srcNoDataValue,
                    dstNodata=dstNoDataValue, callback=callback
                )
                outGdalDataset: gdal.Dataset = gdal.Warp(
                    filename, tmpGdalDataset, options=warpOptions
                )
                assert outGdalDataset is not None

            writer = RasterWriter(outGdalDataset)
            reader = RasterReader(raster)
            if bandList is None:
                bandList = range(1, reader.bandCount() + 1)
            if copyMetadata:
                metadata = reader.metadata()
                writer.setMetadata(metadata)
                for dstBandNo, srcBandNo in enumerate(bandList, 1):
                    # general metadata
                    metadata = reader.metadata(srcBandNo)
                    writer.setMetadata(metadata, dstBandNo)
                    # band name
                    bandName = reader.bandName(srcBandNo)
                    writer.setBandName(bandName, dstBandNo)
                    # spectral info
                    wavelength = reader.wavelength(srcBandNo)
                    writer.setWavelength(wavelength, dstBandNo)
                    fwhm = reader.fwhm(srcBandNo)
                    writer.setFwhm(fwhm, dstBandNo)
                    badBandMultiplier = reader.badBandMultiplier(srcBandNo)
                    writer.setBadBandMultiplier(badBandMultiplier, dstBandNo)

            # clean up ENVI metadata domain (see #1098)
            metadata = reader.metadataDomain('ENVI')
            metadata.pop('wavelength_units', None)
            for key in list(metadata):
                if len(metadata[key]) == reader.bandCount():
                    metadata.pop(key, None)
            writer.setMetadataDomain(metadata, 'ENVI')

            # clean up Default metadata domain (see #1098)
            metadata = reader.metadataDomain()
            metadata.pop('wavelength_units', None)
            for key in [f'Band_{bandNo}' for bandNo in reader.bandNumbers()]:
                metadata.pop(key, None)
            writer.setMetadataDomain(metadata)

            if copyStyle:
                renderer = raster.renderer().clone()
                outraster = QgsRasterLayer(filename)
                outraster.setRenderer(renderer)
                outraster.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)
                del outraster

            writer.setOffset(offset)
            writer.setScale(scale)

            driverShortName = writer.gdalDataset.GetDriver().ShortName
            del writer, outGdalDataset

            if writeEnviHeader:
                if driverShortName in ['GTiff', 'ENVI']:
                    alg = WriteEnviHeaderAlgorithm()
                    parameters = {alg.P_RASTER: filename}
                    self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
