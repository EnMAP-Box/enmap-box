import string
import random
import numpy as np
from os import makedirs
from os.path import join, basename, exists, splitext
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.rasterboundingpolygonalgorithm import RasterBoundingPolygonAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from qgis.core import QgsProcessing, QgsProcessingParameterField, QgsGeometry, QgsVectorLayer, QgsProcessingContext, \
    QgsProcessingFeedback, QgsProcessingException


@typechecked
class TileRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_TILING_SCHEME, _TILING_SCHEME = 'tilingScheme', 'Tiling scheme'
    P_TILE_NAMES, _TILE_NAMES = 'tileNames', 'Tile names'
    P_RESAMPLE_ALG, _RESAMPLE_ALG = 'resampleAlg', 'Resample algorithm'
    P_RESOLUTION, _RESOLUTION = 'resolution', 'Pixel resolution'
    P_NO_DATA_VALUE, _NO_DATA_VALUE = 'noDataValue', 'No data value'
    P_OUTPUT_BASENAME, _OUTPUT_BASENAME = 'outputBasename', 'Output basename'
    P_OUTPUT_FOLDER, _OUTPUT_FOLDER = 'outputFolder', 'Output folder'

    def displayName(self):
        return 'Tile raster layer'

    def shortDescription(self):
        return 'Tile raster data into given tiling scheme.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Source raster layer.'),
            (self._TILING_SCHEME, 'Tiling scheme to be applied.'),
            (self._TILE_NAMES, 'Field with tile names.'),
            (self._RESAMPLE_ALG, 'Spatial resample algorithm.'),
            (self._RESOLUTION, 'Output pixel resolution. If not specified, the original pixel resolution is used.'),
            (self._NO_DATA_VALUE, 'A source no data value needs to be specified, '
                                  'if it is not already specified by the source raster.'),
            (self._OUTPUT_BASENAME, 'Output basename. If not specified, the original basename is used.'),
            (self._OUTPUT_FOLDER, self.FolderDestination)
        ]

    def group(self):
        return Group.AnalysisReadyData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterVectorLayer(
            self.P_TILING_SCHEME, self._TILING_SCHEME, (QgsProcessing.SourceType.TypeVectorPolygon,)
        )
        self.addParameterField(
            self.P_TILE_NAMES, self._TILE_NAMES, None, self.P_TILING_SCHEME,
            QgsProcessingParameterField.DataType.String
        )
        self.addParameterResampleAlg(self.P_RESAMPLE_ALG, self._RESAMPLE_ALG, 0, False, True)
        self.addParameterFloat(self.P_RESOLUTION, self._RESOLUTION, None, True, None, None, True)
        self.addParameterFloat(self.P_NO_DATA_VALUE, self._NO_DATA_VALUE, None, True, None, None, True)
        self.addParameterString(self.P_OUTPUT_BASENAME, self._OUTPUT_BASENAME, None, False, True)
        self.addParameterFolderDestination(self.P_OUTPUT_FOLDER, self._OUTPUT_FOLDER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        tilingScheme = self.parameterAsVectorLayer(parameters, self.P_TILING_SCHEME, context)
        tileNameField = self.parameterAsField(parameters, self.P_TILE_NAMES, context)
        resampleAlg = self.parameterAsGdalResampleAlg(parameters, self.P_RESAMPLE_ALG, context)
        resolution = self.parameterAsFloat(parameters, self.P_RESOLUTION, context)
        sourceNoDataValue = self.parameterAsFloat(parameters, self.P_NO_DATA_VALUE, context)
        baseName = self.parameterAsString(parameters, self.P_OUTPUT_BASENAME, context)
        folderName = self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context)

        if baseName is None:
            baseName = basename(raster.source())
        baseName = splitext(baseName)[0] + '.tif'

        def id_generator(size=40, chars=string.ascii_uppercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

        tmpFolderName = join(folderName, '_tmp', id_generator())
        if not exists(tmpFolderName):
            makedirs(tmpFolderName)
        logFileName = join(tmpFolderName, baseName + '.log')

        with open(logFileName, 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # warp raster into target grid
            reader = RasterReader(raster)
            extent = SpatialExtent(reader.crs(), reader.extent())
            extent2 = extent.toCrs(tilingScheme.crs())
            tilingScheme.selectByRect(extent2)
            geometries = [feature.geometry() for feature in tilingScheme.selectedFeatures()]
            bb = QgsGeometry.unaryUnion(geometries).boundingBox()
            outputBounds = (bb.xMinimum(), bb.yMinimum(), bb.xMaximum(), bb.yMaximum())
            srcNoData = reader.noDataValue(1)
            if srcNoData is None:
                if sourceNoDataValue is None:
                    raise QgsProcessingException(f'specify source no data value: {raster.source()}')
                else:
                    srcNoData = sourceNoDataValue
            if resolution is None:
                xRes = reader.rasterUnitsPerPixelX()
                yRes = reader.rasterUnitsPerPixelY()
            else:
                xRes = resolution
                yRes = resolution

            # feedback.setProgress()

            options = gdal.WarpOptions(
                format='GTiff', dstSRS=tilingScheme.crs().toWkt(), outputBounds=outputBounds,
                creationOptions=Driver.DefaultGTiffCreationOptions, xRes=xRes, yRes=yRes, srcNodata=srcNoData,
                resampleAlg=resampleAlg
            )
            filenameWarpedRaster = join(tmpFolderName, 'warpedRaster.tif')
            gdal.Warp(filenameWarpedRaster, reader.source(), options=options)

            # derive raster bounding polygon
            alg = RasterBoundingPolygonAlgorithm()
            parameters = {
                alg.P_RASTER: filenameWarpedRaster,
                alg.P_GEOMETRY_TYPE: alg.MinimumOrientedRectangle,
                alg.P_OUTPUT_VECTOR: join(tmpFolderName, 'warpedRasterBoundingPolygon.gpkg')
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            vector = QgsVectorLayer(parameters[alg.P_OUTPUT_VECTOR])
            boundingPolygon = list(vector.getFeatures())[0].geometry()

            for feature in tilingScheme.selectedFeatures():

                if not feature.geometry().intersects(boundingPolygon):
                    continue
                tileName = str(feature.attribute(tileNameField))
                filenameTiledRaster = join(folderName, tileName, baseName)
                if not exists(join(folderName, tileName)):
                    makedirs(join(folderName, tileName))
                tileExtent = feature.geometry().boundingBox()
                projWin = tileExtent.xMinimum(), tileExtent.yMaximum(), tileExtent.xMaximum(), tileExtent.yMinimum()
                options = gdal.TranslateOptions(
                    format='GTiff', projWin=projWin, creationOptions=Driver.DefaultGTiffCreationOptions
                )
                if not exists(filenameTiledRaster):
                    ds = gdal.Translate(filenameTiledRaster, filenameWarpedRaster, options=options)

                    # copy metadata
                    writer = RasterWriter(ds)
                    writer.setMetadata(reader.metadata())
                    for bandNo in reader.bandNumbers():
                        writer.setMetadata(reader.metadata(bandNo), bandNo)
                        writer.setBandName(reader.bandName(bandNo), bandNo)
                    writer.close()

                else:
                    # update raster
                    filenameTmp = join(tmpFolderName, 'tiledRaster.vrt')
                    dsNew = gdal.Translate(filenameTmp, filenameWarpedRaster, options=options)
                    ds: gdal.Dataset = gdal.Open(filenameTiledRaster, gdal.GA_Update)
                    for bandNo in reader.bandNumbers():
                        rbNew: gdal.Band = dsNew.GetRasterBand(bandNo)
                        rb: gdal.Band = ds.GetRasterBand(bandNo)
                        arrayNew = rbNew.ReadAsArray()
                        array = rb.ReadAsArray()
                        assert arrayNew.shape == array.shape
                        arrayUpdated = np.where(arrayNew == rbNew.GetNoDataValue(), array, arrayNew)
                        rb.WriteArray(arrayUpdated)
                    dsNew = None
                ds = None
            result = {self.P_OUTPUT_FOLDER: folderName}
            self.toc(feedback, result)

        return result
