from math import ceil, nan, inf
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.numpyutils import NumpyUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis)
from typeguard import typechecked


@typechecked
class AggregateRasterBandsAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_FUNCTION, _FUNCTION = 'function', 'Aggregation functions'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

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
        return 'Aggregate raster layer bands'

    def shortDescription(self) -> str:
        return 'Compute various aggregation functions over all bands, while ignoring no data values.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer with bands to be aggregated.'),
            (self._FUNCTION, 'Functions to be used. '
                             'Number and order of selected functions equals number and order of output bands.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterEnum(self.P_FUNCTION, self._FUNCTION, self.O_FUNCTION, True, None)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        functionIndices = self.parameterAsEnums(parameters, self.P_FUNCTION, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)
            bandCount = len(functionIndices)
            writer = Driver(filename, feedback=feedback).createLike(reader, Qgis.Float32, bandCount)
            noDataValue = Utils.defaultNoDataValue(np.float32)
            lineMemoryUsage = reader.lineMemoryUsage(reader.bandCount() + bandCount, 4)
            blockSizeY = min(raster.height(), ceil(gdal.GetCacheMax() / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
                array = np.array(reader.arrayFromBlock(block), dtype=np.float32)
                mask = reader.maskArray(array)
                invalid = np.logical_not(np.any(mask, axis=0))  # whole pixel is no data (see  #1424)
                array[np.logical_not(mask)] = nan

                if (self.AnyTrueFunction in functionIndices) or self.AllTrueFunction in functionIndices:
                    arrayAsBool = np.logical_and(np.isfinite(array), array)  # take care of NaN and Inf values

                # Calculate all percentiles at once.
                q = [i - self.P0 for i in functionIndices if i >= self.P0]
                for i, outarray in enumerate(NumpyUtils.nanpercentile(array, q)):
                    bandNo = functionIndices.index(q[i] + self.P0) + 1
                    outarray[np.isnan(outarray)] = noDataValue
                    writer.writeArray2d(outarray, bandNo, xOffset=block.xOffset, yOffset=block.yOffset)

                # Calculate all other indices individually.
                for bandNo, functionIndex in enumerate(functionIndices, 1):
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
                    assert outarray.dtype == np.float32, self.O_FUNCTION[functionIndex]
                    outarray[np.isnan(outarray)] = noDataValue

                    # explicitely mask pixel with all-no-data (see #1424)
                    outarray[invalid] = noDataValue

                    # write result
                    writer.writeArray2d(outarray, bandNo, xOffset=block.xOffset, yOffset=block.yOffset)

            for bandNo, functionIndex in enumerate(functionIndices, 1):
                bandName = self.O_FUNCTION[functionIndex]
                writer.setBandName(bandName, bandNo)

            writer.setNoDataValue(noDataValue)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
