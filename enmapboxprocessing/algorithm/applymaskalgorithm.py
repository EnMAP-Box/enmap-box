from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.layertomaskalgorithm import LayerToMaskAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer)
from typeguard import typechecked


@typechecked
class ApplyMaskAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_MASK, _MASK = 'mask', 'Mask layer'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self):
        return 'Apply mask layer to raster layer'

    def shortDescription(self):
        return 'Areas where the mask layer evaluates to false are set to the source no data value (0, if undefined).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Source raster layer.'),
            (self._MASK, 'A mask layer.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Masking.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterMapLayer(self.P_MASK, self._MASK)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        mask = self.parameterAsLayer(parameters, self.P_MASK, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            alg = LayerToMaskAlgorithm()
            parameters = {
                alg.P_LAYER: mask,
                alg.P_GRID: raster,
                alg.P_OUTPUT_MASK: Utils.tmpFilename(filename, 'mask.tif')
            }
            mask = QgsRasterLayer(self.runAlg(alg, parameters, None, feedback2, context, True)[alg.P_OUTPUT_MASK])

            # read mask
            invalid = RasterReader(mask).array()[0] == 0

            # process raster
            reader = RasterReader(raster)
            writer = Driver(filename, feedback=feedback).createLike(reader, reader.dataType())
            for i in range(reader.bandCount()):
                feedback.setProgress(i / reader.bandCount() * 100)
                array = reader.array(bandList=[i + 1])[0]
                noDataValue = reader.noDataValue(i + 1)
                array[invalid] = noDataValue
                writer.writeArray(array[None], bandList=[i + 1])

                writer.setBandName(reader.bandName(i + 1), i + 1)
                writer.setMetadata(reader.metadata(i + 1), i + 1)
                writer.setNoDataValue(noDataValue, i + 1)

            writer.setMetadata(reader.metadata())
            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
