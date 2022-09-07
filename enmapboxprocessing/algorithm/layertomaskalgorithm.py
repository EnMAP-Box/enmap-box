from typing import Tuple, List, Dict, Any

from enmapboxprocessing.algorithm.rasterizevectoralgorithm import RasterizeVectorAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import Group, EnMAPProcessingAlgorithm
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsProcessingException, \
    QgsVectorLayer
from typeguard import typechecked


@typechecked
class LayerToMaskAlgorithm(EnMAPProcessingAlgorithm):
    P_LAYER, _LAYER = 'raster', 'Layer'
    P_GRID, _GRID = 'grid', 'Grid'
    P_OUTPUT_MASK, _OUTPUT_MASK = 'outputMask', 'Output mask raster layer'

    def displayName(self) -> str:
        return 'Layer to mask raster layer '

    def group(self):
        return Group.Test.value + Group.Masking.value

    def shortDescription(self) -> str:
        return 'Interprete a layer as a mask layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._LAYER, 'A layer to be interpreted as a mask layer.'),
            (self._GRID, 'The target grid. Can be skipped if the source layer is a raster layer.'),
            (self._OUTPUT_MASK, self.RasterFileDestination)
        ]

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterMapLayer(self.P_LAYER, self._LAYER)
        self.addParameterRasterLayer(self.P_GRID, self._GRID, optional=True)
        self.addParameterRasterDestination(self.P_OUTPUT_MASK, self._OUTPUT_MASK)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        layer = self.parameterAsLayer(parameters, self.P_LAYER, context)
        grid = self.parameterAsRasterLayer(parameters, self.P_GRID, context)
        if grid is None:
            if not isinstance(layer, QgsRasterLayer):
                message = f'Missing parameter: {self._GRID}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)
            grid = layer
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_MASK, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if isinstance(layer, QgsRasterLayer):
                feedback.pushInfo('Prepare mask')
                alg = TranslateRasterAlgorithm()
                parameters = {
                    alg.P_RASTER: layer,
                    alg.P_GRID: grid,
                    alg.P_CREATION_PROFILE: self.DefaultVrtCreationProfile,
                    alg.P_BAND_LIST: [layer.renderer().usesBands()[0]],
                    alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'band.vrt')
                }
                raster = QgsRasterLayer(
                    self.runAlg(alg, parameters, None, feedback2, context, True)[alg.P_OUTPUT_RASTER])
                reader = RasterReader(raster)
                array = reader.array()
                marray = reader.maskArray(array, defaultNoDataValue=0)
                Driver(filename, feedback=feedback).createFromArray(marray, reader.extent(), reader.crs())
            elif isinstance(layer, QgsVectorLayer):
                feedback.pushInfo('Prepare mask')
                alg = RasterizeVectorAlgorithm()
                parameters = {
                    alg.P_VECTOR: layer,
                    alg.P_GRID: grid,
                    alg.P_INIT_VALUE: 0,
                    alg.P_BURN_VALUE: 1,
                    alg.P_DATA_TYPE: self.Byte,
                    alg.P_OUTPUT_RASTER: filename
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
            else:
                raise QgsProcessingException(f'unsupported layer type: {layer}')

            result = {self.P_OUTPUT_MASK: filename}
            self.toc(feedback, result)

        return result
