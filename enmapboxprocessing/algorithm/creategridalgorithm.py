from typing import Dict, Any, List, Tuple

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, Qgis
from typeguard import typechecked


@typechecked
class CreateGridAlgorithm(EnMAPProcessingAlgorithm):
    P_CRS, _CRS = 'crs', 'CRS'
    P_EXTENT, _EXTENT = 'extent', 'Extent'
    P_UNIT, _UNIT = 'unit', 'Size units'
    O_UNIT = ['Pixels', 'Georeferenced units']
    PixelUnits, GeoreferencedUnits = range(2)
    P_WIDTH, _WIDTH = 'width', 'Width / horizontal resolution'
    P_HEIGHT, _HEIGHT = 'hight', 'Height / vertical resolution'
    P_OUTPUT_GRID, _OUTPUT_GRID = 'outputGrid', 'Output grid'

    def displayName(self):
        return 'Create grid'

    def shortDescription(self):
        return 'Create an empty raster that can be used as a grid.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CRS, 'Destination coordinate reference system.'),
            (self._EXTENT, 'Destination extent.'),
            (self._UNIT, 'Units to use when defining target raster size/resolution.'),
            (self._WIDTH, 'Target width if size units is "Pixels", '
                          'or horizontal resolution if size units is "Georeferenced units".'),
            (self._HEIGHT, 'Target height if size units is "Pixels", '
                           'or vertical resolution if size units is "Georeferenced units".'),
            (self._OUTPUT_GRID, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterMiscellaneous.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterCrs(self.P_CRS, self._CRS)
        self.addParameterExtent(self.P_EXTENT, self._EXTENT)
        self.addParameterEnum(self.P_UNIT, self._UNIT, self.O_UNIT)
        self.addParameterFloat(self.P_WIDTH, self._WIDTH, 0, minValue=0)
        self.addParameterFloat(self.P_HEIGHT, self._HEIGHT, 0, minValue=0)
        self.addParameterVrtDestination(self.P_OUTPUT_GRID, self._OUTPUT_GRID)

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        unit = self.parameterAsEnum(parameters, self.P_UNIT, context)
        if unit == self.PixelUnits:
            if self.parameterAsInt(parameters, self.P_WIDTH, context) < 1:
                return False, 'Width must be greater than or equal to 1 pixel.'
            if self.parameterAsInt(parameters, self.P_HEIGHT, context) < 1:
                return False, 'Height must be greater than or equal to 1 pixel.'
        if unit == self.GeoreferencedUnits:
            if self.parameterAsDouble(parameters, self.P_WIDTH, context) == 0:
                return False, 'Horizontal resolution must be greater than 0.'
            if self.parameterAsDouble(parameters, self.P_HEIGHT, context) == 0:
                return False, 'Vertical resolution must be greater than 0.'
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:

        crs = self.parameterAsCrs(parameters, self.P_CRS, context)
        extent = self.parameterAsExtent(parameters, self.P_EXTENT, context, crs=crs)
        unit = self.parameterAsEnum(parameters, self.P_UNIT, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_GRID, context)
        if unit == self.PixelUnits:
            width = self.parameterAsInt(parameters, self.P_WIDTH, context)
            height = self.parameterAsInt(parameters, self.P_HEIGHT, context)
        elif unit == self.GeoreferencedUnits:
            xres = self.parameterAsDouble(parameters, self.P_WIDTH, context)
            width = int(round(extent.width() / xres, 0))
            yres = self.parameterAsDouble(parameters, self.P_HEIGHT, context)
            height = int(round(extent.height() / yres, 0))
        else:
            assert 0

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)
            Driver(filename, self.VrtFormat, None, feedback).create(Qgis.Byte, width, height, 1, extent, crs)
            result = {self.P_OUTPUT_GRID: filename}
            self.toc(feedback, result)

        return result
