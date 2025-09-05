from math import ceil, nan, inf
from os import makedirs
from os.path import join, exists, splitext
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsProcessing, \
    QgsRasterLayer, Qgis

from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.numpyutils import NumpyUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils


@typechecked
class AggregateRastersAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTERS, _RASTERS = 'rasters', 'Raster layers'
    P_MASKS, _MASKS = 'masks', 'Mask layers'
    P_FUNCTION, _FUNCTION = 'function', 'Aggregation functions'
    P_GRID, _GRID = 'grid', 'Grid'
    P_OUTPUT_BASENAME, _OUTPUT_BASENAME = 'outputBasename', 'Output basename'
    P_OUTPUT_FOLDER, _OUTPUT_FOLDER = 'outputFolder', 'Output folder'

    O_FUNCTION = [
        'arithmetic mean', 'standard deviation', 'variance', 'minimum', 'median', 'maximum', 'sum', 'product',
        'range', 'interquartile range', 'any true', 'all true', 'arg minimum', 'arg maximum'
    ]
    (
        ArithmeticMeanFunction, StandardDeviationFunction, VarianceFunction, MinimumFunction, MedianFunction,
        MaximumFunction, SumFunction, ProductFunction, RangeFunction, InterquartileRangeFunction, AnyTrueFunction,
        AllTrueFunction, ArgMinimumFunction, ArgMaximumFunction
    ) = range(len(O_FUNCTION))
    P0 = len(O_FUNCTION)
    O_FUNCTION.extend([f'{i}-th percentile' for i in range(101)])

    def displayName(self) -> str:
        return 'Aggregate raster layers'

    def shortDescription(self) -> str:
        return 'Compute various aggregation functions over a list of rasters, while ignoring no data values.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTERS, 'A list of raster layers with bands to be aggregated.'),
            (self._FUNCTION, 'Functions to be used.'),
            (self._OUTPUT_BASENAME, 'The output basename used to write into the output folder. '
                                    'For a basename like "myRaster.tif", each aggregation is written into an '
                                    'individual file named "myRaster.{function}.tif".'),
            (self._GRID, 'Reference grid specifying the destination extent, pixel size and projection. '
                         'If not defined, first raster is used as grid.'),
            (self._MASKS, 'A list of external raster mask layers.'),
            (self._OUTPUT_FOLDER, self.FolderDestination)
        ]

    def group(self):
        return Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterMultipleLayers(self.P_RASTERS, self._RASTERS, QgsProcessing.SourceType.TypeRaster)
        self.addParameterEnum(self.P_FUNCTION, self._FUNCTION, self.O_FUNCTION, True, None)
        self.addParameterString(self.P_OUTPUT_BASENAME, self._OUTPUT_BASENAME)
        self.addParameterMultipleLayers(
            self.P_MASKS, self._MASKS, QgsProcessing.SourceType.TypeRaster, None, True, True
        )
        self.addParameterRasterLayer(self.P_GRID, self._GRID, None, True, True)
        self.addParameterFolderDestination(self.P_OUTPUT_FOLDER, self._OUTPUT_FOLDER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        rasters: List[QgsRasterLayer] = self.parameterAsLayerList(parameters, self.P_RASTERS, context)
        masks: List[QgsRasterLayer] = self.parameterAsLayerList(parameters, self.P_MASKS, context)
        grid = self.parameterAsRasterLayer(parameters, self.P_GRID, context)
        functionIndices = self.parameterAsEnums(parameters, self.P_FUNCTION, context)
        basename = self.parameterAsString(parameters, self.P_OUTPUT_BASENAME, context)
        foldername = self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context)

        if masks is not None and len(masks) != len(rasters):
            raise QgsProcessingFeedback('Number of masks does not match number of rasters.')

        if grid is None:
            grid = rasters[0]
        gridReader = RasterReader(grid)

        if not exists(foldername):
            makedirs(foldername)

        with (open(join(basename + '.log'), 'w') as logfile):
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            bandCount = rasters[0].bandCount()
            readers: List[RasterReader] = list()
            mreaders: List[RasterReader] = list()
            for i, raster in enumerate(rasters):
                if raster.bandCount() != bandCount:
                    raise QgsProcessingException(
                        'Band count mismatch: all rasters must contain the same number of bands.'
                    )
                readers.append(RasterReader(raster, crs=grid.crs()))
                if masks is not None:
                    if masks[i].bandCount() != 1:
                        raise QgsProcessingException('All masks must be single band rasters.')
                    mreaders.append(RasterReader(masks[i], crs=grid.crs()))

            noDataValue = Utils.defaultNoDataValue(np.float32)
            writers: List[RasterWriter] = list()
            for functionIndex in functionIndices:
                functionName = self.O_FUNCTION[functionIndex].replace(' ', '_')
                filename = join(foldername, f'{splitext(basename)[0]}.{functionName}{splitext(basename)[1]}')
                writer = Driver(filename, feedback=feedback).createLike(
                    gridReader, Qgis.DataType.Float32, bandCount
                )
                writer.setNoDataValue(noDataValue)
                for bandNo in readers[0].bandNumbers():
                    writer.setBandName(readers[0].bandName(bandNo), bandNo)
                    writer.setWavelength(readers[0].wavelength(bandNo), bandNo)
                writers.append(writer)

            lineMemoryUsage = gridReader.lineMemoryUsage(len(writers) + len(readers), 4)
            blockSizeY = min(raster.height(), ceil(gdal.GetCacheMax() / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in gridReader.walkGrid(blockSizeX, blockSizeY, feedback):

                if masks is not None:
                    externalMasks = list()
                    for mreader in mreaders:
                        a = mreader.arrayFromBlock(block)
                        m = mreader.maskArray(a, defaultNoDataValue=0)
                        externalMasks.append(m)

                for bandNo in readers[0].bandNumbers():
                    array = list()
                    mask = list()
                    for i, reader in enumerate(readers):
                        iarray = reader.arrayFromBlock(block, [bandNo])
                        imask = reader.maskArray(iarray, [bandNo])
                        if masks is not None:
                            imask = np.logical_and(imask, externalMasks[i])
                        array.append(iarray[0])
                        mask.append(imask[0])
                    array = np.array(array, np.float32)
                    invalid = np.logical_not(np.any(mask, axis=0))  # whole pixel is no data
                    array[np.logical_not(mask)] = nan

                    if self.AnyTrueFunction in functionIndices or self.AllTrueFunction in functionIndices:
                        arrayAsBool = np.logical_and(np.isfinite(array), array)  # take care of NaN and Inf values

                    # Calculate all percentiles at once.
                    q = [i - self.P0 for i in functionIndices if i >= self.P0]
                    for i, outarray in enumerate(NumpyUtils.nanpercentile(array, q)):
                        writer = writers[functionIndices.index(q[i] + self.P0)]
                        outarray[np.isnan(outarray)] = noDataValue
                        outarray[invalid] = noDataValue
                        writer.writeArray2d(outarray, bandNo, xOffset=block.xOffset, yOffset=block.yOffset)

                    # Calculate all other indices individually.
                    for functionIndex, writer in zip(functionIndices, writers):
                        if functionIndex >= self.P0:  # skip percentiles
                            continue
                        elif functionIndex == self.ArithmeticMeanFunction:
                            outarray = np.nanmean(array, axis=0)
                        elif functionIndex == self.StandardDeviationFunction:
                            outarray = np.nanstd(array, axis=0)
                        elif functionIndex == self.VarianceFunction:
                            outarray = np.nanvar(array, axis=0)
                        elif functionIndex == self.MinimumFunction:
                            outarray = np.nanmin(array, axis=0)
                        elif functionIndex == self.MedianFunction:
                            outarray = np.nanmedian(array, axis=0)
                        elif functionIndex == self.MaximumFunction:
                            outarray = np.nanmax(array, axis=0)
                        elif functionIndex == self.SumFunction:
                            outarray = np.nansum(array, axis=0)
                        elif functionIndex == self.ProductFunction:
                            outarray = np.nanprod(array, axis=0)
                        elif functionIndex == self.RangeFunction:
                            outarray = np.nanmax(array, axis=0) - np.nanmin(array, axis=0)
                        elif functionIndex == self.InterquartileRangeFunction:
                            p25, p75 = NumpyUtils.nanpercentile(array, [25, 75])
                            outarray = p75 - p25
                        elif functionIndex == self.AnyTrueFunction:
                            outarray = np.any(arrayAsBool, axis=0).astype(np.float32)
                        elif functionIndex == self.AllTrueFunction:
                            outarray = np.all(arrayAsBool, axis=0).astype(np.float32)
                        elif functionIndex == self.ArgMinimumFunction:
                            # Numpy nanargmin will throw an All-NaN slice encountered ValueError, instead of just a warning.
                            # Append a inf band to prevent this.
                            array2 = list(array)
                            array2.append(np.full_like(array[0], inf))
                            outarray = np.nanargmin(array2, axis=0).astype(np.float32)
                            # Now, set All-NaN slice pixel to nan.
                            outarray[outarray == len(array)] = nan
                        elif functionIndex == self.ArgMaximumFunction:
                            # Numpy nanargmax will throw an All-NaN slice encountered ValueError, instead of just a warning.
                            # Append a -inf band to prevent this.
                            array2 = list(array)
                            array2.append(np.full_like(array[0], -inf))
                            outarray = np.nanargmax(array2, axis=0).astype(np.float32)
                            # Now, set All-NaN slice pixel to nan.
                            outarray[outarray == len(array)] = nan
                        else:
                            raise ValueError()

                        # replace nan values by no data values
                        outarray[np.isnan(outarray)] = noDataValue

                        # explicitely mask pixel with all-no-data (see #1424)
                        outarray[invalid] = noDataValue

                        # write result
                        writer.writeArray2d(outarray, bandNo, xOffset=block.xOffset, yOffset=block.yOffset)

            for writer in writers:
                writer.close()

            result = {self.P_OUTPUT_FOLDER: foldername}
            self.toc(feedback, result)

        return result
