from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsCoordinateReferenceSystem)
from typeguard import typechecked


@typechecked
class GeolocateRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_X_RASTER, _X_RASTER = 'xRaster', 'X locations raster layer'
    P_Y_RASTER, _Y_RASTER = 'yRaster', 'Y locations raster layer'
    P_CRS, _CRS = 'crs', 'Locations CRS'
    P_GRID, _GRID = 'grid', 'Grid'
    P_NO_DATA_VALUE, _NO_DATA_VALUE = 'noDataValue', 'No data value'
    P_X_BAND, _X_BAND = 'xBand', 'X locations band'
    P_Y_BAND, _Y_BAND = 'yBand', 'Y locations band'
    P_PIXEL_OFFSET, _PIXEL_OFFSET = 'pixelOffset', 'Pixel offset'
    P_LINE_OFFSET, _LINE_OFFSET = 'lineOffset', 'Line offset'
    P_PIXEL_STEP, _PIXEL_STEP = 'pixelStep', 'Pixel step'
    P_LINE_STEP, _LINE_STEP = 'lineStep', 'Line step'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputGeolocatedRaster', 'Output raster layer'

    def displayName(self):
        return 'Geolocate raster layer'

    def shortDescription(self):
        link = self.htmlLink('https://gdal.org/development/rfc/rfc4_geolocate.html', 'Geolocation Arrays')
        return 'Geolocate a raster layer using geolocation arrays. ' \
               f'See {link} in the GDAL documentation for details on the concept and parameters.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer to be geolocated.'),
            (self._X_RASTER, 'A raster layer containing the x geolocation array.'),
            (self._Y_RASTER, 'A raster layer containing the y geolocation array.'),
            (self._CRS, 'The coordinate reference system of the geolocation arrays.'),
            (self._GRID, 'The destination grid. '
                         'If skipped, the grid CRS is set to the CRS of the geolocation arrays, '
                         'extent and resolution is controlled by gdal.Warp defaults.'),
            (self._NO_DATA_VALUE, 'Value used to fill no data regions introduced by warping.'),
            (self._X_BAND, 'The x coordinates band.'),
            (self._Y_BAND, 'The y coordinates band.'),
            (self._PIXEL_OFFSET, 'Pixel offset into geo-located data of left geolocation pixel.'),
            (self._LINE_OFFSET, 'Line offset into geo-located data of top geolocation pixel.'),
            (self._PIXEL_STEP, 'Each geolocation pixel represents this many geolocated pixels.'),
            (self._LINE_STEP, 'Each geolocation pixel represents this many geolocated lines.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterProjections.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterRasterLayer(self.P_X_RASTER, self._X_RASTER)
        self.addParameterRasterLayer(self.P_Y_RASTER, self._Y_RASTER)
        self.addParameterRasterLayer(self.P_GRID, self._GRID, optional=True)
        self.addParameterCrs(self.P_CRS, self._CRS, QgsCoordinateReferenceSystem.fromEpsgId(4326), True, True)
        self.addParameterInt(self.P_NO_DATA_VALUE, self._NO_DATA_VALUE, None, True)
        self.addParameterBand(self.P_X_BAND, self._X_BAND, None, self.P_X_RASTER, True, False, True)
        self.addParameterBand(self.P_Y_BAND, self._Y_BAND, None, self.P_Y_RASTER, True, False, True)
        self.addParameterInt(self.P_PIXEL_OFFSET, self._PIXEL_OFFSET, 0, True, None, None, True)
        self.addParameterInt(self.P_LINE_OFFSET, self._LINE_OFFSET, 0, True, None, None, True)
        self.addParameterInt(self.P_PIXEL_STEP, self._PIXEL_STEP, 1, True, None, None, True)
        self.addParameterInt(self.P_LINE_STEP, self._LINE_STEP, 1, True, None, None, True)
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        xraster = self.parameterAsRasterLayer(parameters, self.P_X_RASTER, context)
        yraster = self.parameterAsRasterLayer(parameters, self.P_Y_RASTER, context)
        crs = self.parameterAsCrs(parameters, self.P_CRS, context)
        grid = self.parameterAsRasterLayer(parameters, self.P_GRID, context)
        noDataValue = self.parameterAsInt(parameters, self.P_NO_DATA_VALUE, context)
        xband = self.parameterAsInt(parameters, self.P_X_BAND, context)
        yband = self.parameterAsInt(parameters, self.P_Y_BAND, context)
        pixelOffset = self.parameterAsInt(parameters, self.P_PIXEL_OFFSET, context)
        lineOffset = self.parameterAsInt(parameters, self.P_LINE_OFFSET, context)
        pixelStep = self.parameterAsInt(parameters, self.P_PIXEL_STEP, context)
        lineStep = self.parameterAsInt(parameters, self.P_LINE_STEP, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        assert filename.endswith('.vrt')

        if xband is None:
            xband = 1
        if yband is None:
            yband = 1

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # prepare geolocated dataset
            xfilename = Utils.sidecarFilename(filename, '.xloc.vrt')
            yfilename = Utils.sidecarFilename(filename, '.yloc.vrt')
            zfilename = Utils.sidecarFilename(filename, '.data.vrt')
            gdal.Translate(xfilename, xraster.source(), format='VRT', bandList=[xband])
            gdal.Translate(yfilename, yraster.source(), format='VRT', bandList=[yband])
            reader = RasterReader(raster)
            ds = gdal.Translate(zfilename, raster.source(), format='VRT', noData=noDataValue)
            writer = RasterWriter(ds)
            writer.setMetadataItem('SRS', crs.toWkt(), 'GEOLOCATION')
            writer.setMetadataItem('X_DATASET', xfilename, 'GEOLOCATION')
            writer.setMetadataItem('X_BAND', 1, 'GEOLOCATION')
            writer.setMetadataItem('Y_DATASET', yfilename, 'GEOLOCATION')
            writer.setMetadataItem('Y_BAND', 1, 'GEOLOCATION')
            writer.setMetadataItem('PIXEL_OFFSET', pixelOffset, 'GEOLOCATION')
            writer.setMetadataItem('LINE_OFFSET', lineOffset, 'GEOLOCATION')
            writer.setMetadataItem('PIXEL_STEP', pixelStep, 'GEOLOCATION')
            writer.setMetadataItem('LINE_STEP', lineStep, 'GEOLOCATION')
            writer.close()
            ds = None

            # apply geolocations by warping
            # ds = gdal.Warp(filename, zfilename, geoloc=True, dstSRS=crs.toWkt(), xRes=0.0001, yRes=0.0001)
            if grid is None:
                ds = gdal.Warp(filename, zfilename, geoloc=True, srcSRS=crs.toWkt(), dstSRS=crs.toWkt())
            else:
                width = RasterReader(grid).width()
                height = RasterReader(grid).height()
                extent = grid.extent()
                outputBounds = (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())
                warpOptions = gdal.WarpOptions(
                    format='VRT', width=width, height=height, outputBounds=outputBounds, srcSRS=crs.toWkt(),
                    dstSRS=grid.crs().toWkt(), geoloc=True)
                ds = gdal.Warp(filename, zfilename, options=warpOptions)

            # set metadata
            writer = RasterWriter(ds)
            writer.setMetadata(reader.metadata())
            for bandNo in range(1, reader.bandCount() + 1):
                writer.setMetadata(reader.metadata(bandNo), bandNo)
                writer.setBandName(reader.bandName(bandNo), bandNo)
                writer.setNoDataValue(reader.noDataValue(bandNo), bandNo)
                writer.setOffset(reader.offset(bandNo), bandNo)
                writer.setScale(reader.scale(bandNo), bandNo)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
