import inspect
from inspect import signature
from typing import Dict, Any, List, Tuple, Optional

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis)
from typeguard import typechecked


@typechecked
class ApplyBandFunctionAlgorithmBase(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_FUNCTION, _FUNCTION = 'function', 'Function'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Raster layer to be processed band-wise.'),
            (self._FUNCTION, self.helpParameterCode()),
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
        raise NotImplementedError()

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterCode(self.P_FUNCTION, self._FUNCTION, self.defaultCodeAsString())
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsFunction(self, parameters: Dict[str, Any], name, context: QgsProcessingContext):
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        function = namespace['function']
        return function

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        function = self.parameterAsFunction(parameters, self.P_FUNCTION, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            feedback.pushInfo('Apply function')
            self.reader = RasterReader(raster)
            self.writer = Driver(filename, feedback=feedback).createLike(self.reader, self.outputDataType())
            for i in range(self.reader.bandCount()):
                feedback.setProgress(i / self.reader.bandCount() * 100)
                bandList = [i + 1]
                self.array = self.reader.array(bandList=bandList)[0]
                self.prepareInput()
                self.marray = self.reader.maskArray(self.array[None], bandList=bandList)[0]
                if len(signature(function).parameters) == 1:
                    self.outarray = function(self.array)
                else:
                    self.outarray = function(self.array, self.reader.noDataValue(i + 1))
                self.prepareOutput()
                self.writer.writeArray(self.outarray[None], bandList=bandList)

            self.writer.setMetadata(self.reader.metadata())
            self.writer.setNoDataValue(self.outputNoDataValue())
            for i in range(self.reader.bandCount()):
                self.writer.setBandName(self.reader.bandName(i + 1), i + 1)
            self.writer.close()

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result

    def outputDataType(self) -> Qgis.DataType:
        return Qgis.Float32

    def outputNoDataValue(self) -> Optional[float]:
        return None

    def prepareInput(self):
        pass

    def prepareOutput(self):
        pass
