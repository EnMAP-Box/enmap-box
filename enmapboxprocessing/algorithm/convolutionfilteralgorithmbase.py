import inspect
import traceback
from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis)
from typeguard import typechecked


@typechecked
class ConvolutionFilterAlgorithmBase(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_KERNEL, _KERNEL = 'kernel', 'Kernel'
    P_NORMALIZE, _NORMALIZE = 'normalize', 'Normalize kernel'
    P_INTERPOLATE, _INTERPOLATE = 'interpolate', 'Interpolate no data pixel'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer to be filtered.'),
            (self._KERNEL, self.helpParameterCode()),
            (self._NORMALIZE, 'Whether to normalize the kernel to have a sum of one.'),
            (self._INTERPOLATE, 'Whether to interpolate no data pixel. '
                                'Will result in renormalization of the kernel at each position ignoring '
                                'pixels with no data values.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def displayName(self) -> str:
        raise NotImplementedError()

    def shortDescription(self) -> str:
        raise NotImplementedError()

    def code(self):
        raise NotImplementedError()

    def helpParameterCode(self) -> str:
        raise NotImplementedError()

    def group(self):
        return Group.Test.value + Group.ConvolutionMorphologyAndFiltering.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterCode(self.P_KERNEL, self._KERNEL, self.defaultCodeAsString())
        self.addParameterBoolean(self.P_NORMALIZE, self._NORMALIZE, False, False, True)
        self.addParameterBoolean(self.P_INTERPOLATE, self._INTERPOLATE, True, False, True)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsKernel(self, parameters: Dict[str, Any], name, context: QgsProcessingContext):
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        kernel = namespace['kernel']
        return kernel

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        valid, message = super().checkParameterValues(parameters, context)
        if not valid:
            return valid, message
        # check code
        try:
            from astropy.convolution import Kernel
            kernel = self.parameterAsKernel(parameters, self.P_KERNEL, context)
            assert isinstance(kernel, Kernel)
            assert 1 <= kernel.dimension <= 3
        except Exception:
            return False, traceback.format_exc()
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        kernel = self.parameterAsKernel(parameters, self.P_KERNEL, context)
        normalize_kernel = self.parameterAsBoolean(parameters, self.P_NORMALIZE, context)
        if self.parameterAsBoolean(parameters, self.P_INTERPOLATE, context):
            nan_treatment = 'interpolate'
        else:
            nan_treatment = 'fill'
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        maximumMemoryUsage = Utils.maximumMemoryUsage()

        with open(filename + '.log', 'w') as logfile:
            from astropy.convolution import convolve, CustomKernel
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            feedback.pushInfo(f'Filter kernel {list(kernel.array.shape)}: {kernel.array.tolist()}')
            if kernel.dimension == 3:
                pass
            elif kernel.dimension == 2:
                kernel = CustomKernel(array=kernel.array[None])
            elif kernel.dimension == 1:
                kernel = CustomKernel(array=kernel.array.reshape(-1, 1, 1))

            zsize, ysize, xsize = kernel.shape
            overlap = int((max(ysize, xsize) + 1) / 2.)

            feedback.pushInfo('Convolve raster')
            rasterReader = RasterReader(raster)
            writer = Driver(filename, feedback=feedback).createLike(rasterReader, Qgis.Float32)
            lineMemoryUsage = rasterReader.lineMemoryUsage(dataTypeSize=Qgis.Float32)
            lineMemoryUsage *= 2  # output has same size
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in rasterReader.walkGrid(blockSizeX, blockSizeY, feedback):
                feedback.setProgress(block.yOffset / rasterReader.height() * 100)
                array = rasterReader.arrayFromBlock(block, overlap=overlap)
                mask = rasterReader.maskArray(array)
                outarray = convolve(
                    array, kernel, fill_value=np.nan, nan_treatment=nan_treatment,
                    normalize_kernel=normalize_kernel, mask=np.logical_not(mask)
                )
                noDataValue = float(np.finfo(np.float32).min)
                outarray[np.isnan(outarray)] = noDataValue
                writer.writeArray(outarray, block.xOffset, block.yOffset, overlap=overlap)

            writer.setMetadata(rasterReader.metadata())
            writer.setNoDataValue(noDataValue)
            for i in range(rasterReader.bandCount()):
                writer.setBandName(rasterReader.bandName(i + 1), i + 1)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
