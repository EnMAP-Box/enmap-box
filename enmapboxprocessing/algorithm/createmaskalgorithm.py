from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)


@typechecked
class CreateMaskAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_BAND, _BAND = 'band', 'Band'
    P_MASK_NO_DATA_VALUES, _MASK_NO_DATA_VALUES = 'maskNoDataValues', 'Mask no data values'
    P_MASK_NONFINITE_VALUES, _MASK_NONFINITE_VALUES = 'maskNonFiniteValues', 'Mask non-finite values'
    P_MASK_VALUES, _MASK_VALUES = 'maskValues', 'Mask values'
    P_MASK_VALUE_RANGES, _MASK_VALUE_RANGES = 'maskValueRanges', 'Mask value ranges'
    P_MASK_BITS, _MASK_BITS = 'maskBits', 'Mask bits'
    P_OUTPUT_MASK, _OUTPUT_MASK = 'outputMask', 'Output mask raster layer'

    def displayName(self) -> str:
        return 'Create mask raster layer'

    def shortDescription(self) -> str:
        return 'Create a mask raster layer by evaluating a source raster layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer.'),
            (self._BAND, 'Band to be evaluated.'),
            (self._MASK_NO_DATA_VALUES, 'Whether to mask no data values.'),
            (self._MASK_NONFINITE_VALUES, 'Whether to mask non-finite values (i.e. Inf and NaN).'),
            (self._MASK_VALUES, 'Values to be masked.'),
            (self._MASK_VALUE_RANGES, 'Value-ranges to be masked.'),
            (self._MASK_BITS, 'Bits to be masked. A bit mask part is specified by the "First bit", the "Bit count" '
                              'and a list of "Values" (space- or comma-separated) to be masked.'),
            (self._OUTPUT_MASK, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Masking.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBand(self.P_BAND, self._BAND, None, self.P_RASTER)
        self.addParameterBoolean(self.P_MASK_NO_DATA_VALUES, self._MASK_NO_DATA_VALUES, True, True)
        self.addParameterBoolean(self.P_MASK_NONFINITE_VALUES, self._MASK_NONFINITE_VALUES, True, True)
        self.addParameterMatrix(self.P_MASK_VALUES, self._MASK_VALUES, 0, False, ['Value'], None, True)
        self.addParameterMatrix(
            self.P_MASK_VALUE_RANGES, self._MASK_VALUE_RANGES, 0, False, ['Minimum', 'Maximum'], None, True
        )
        self.addParameterMatrix(
            self.P_MASK_BITS, self._MASK_BITS, 0, False, ['First bit', 'Bit count', 'Values'], None, True
        )
        self.addParameterRasterDestination(self.P_OUTPUT_MASK, self._OUTPUT_MASK)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        bandNo = self.parameterAsBand(parameters, self.P_BAND, context)
        maskNoDataValues = self.parameterAsBoolean(parameters, self.P_MASK_NO_DATA_VALUES, context)
        maskNonFiniteValues = self.parameterAsBoolean(parameters, self.P_MASK_NONFINITE_VALUES, context)
        maskValues = self.parameterAsMatrix(parameters, self.P_MASK_VALUES, context)
        maskValueRanges = self.parameterAsMatrix(parameters, self.P_MASK_VALUE_RANGES, context)
        maskBits = self.parameterAsMatrix(parameters, self.P_MASK_BITS, context)

        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_MASK, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)
            array = np.array(reader.array(bandList=[bandNo]))
            maskArray = np.array(reader.maskArray(array, [bandNo], maskNonFiniteValues, None, maskNoDataValues))

            if maskValues is not None:
                maskValues = np.array(maskValues, array.dtype)
                for value in maskValues:
                    maskArray[array == value] = False

            if maskValueRanges is not None:
                maskValueRanges = np.array(maskValueRanges, array.dtype).reshape((-1, 2))
                for vmin, vmax in maskValueRanges:
                    maskArray[np.logical_and(vmin <= array, array <= vmax)] = False

            if maskBits is not None:
                maskBits = np.array(maskBits).reshape((-1, 3))
                for first_bit, bit_count, values in maskBits:
                    first_bit = int(first_bit)
                    bit_count = int(bit_count)
                    values = [int(v) for v in values.replace(',', ' ').split(' ') if v != '']

                    bitmask = (1 << bit_count) - 1
                    arrayShifted = array >> first_bit
                    arrayShiftedAndMasked = arrayShifted & bitmask
                    for value in values:
                        maskArray[arrayShiftedAndMasked == value] = False

            writer = Driver(filename).createFromArray(maskArray, reader.extent(), reader.crs())
            writer.close()
            result = {self.P_OUTPUT_MASK: filename}
            self.toc(feedback, result)

        return result
