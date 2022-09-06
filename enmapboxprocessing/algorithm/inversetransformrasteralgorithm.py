from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis)
from typeguard import typechecked


@typechecked
class InverseTransformRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_TRANSFORMER, _TRANSFORMER = 'transformer', 'Transformer'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Inverse transform raster layer'

    def shortDescription(self) -> str:
        return 'Uses a fitted transformer to inverse transform a raster layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'The raster layer to be inverse transformed.'),
            (self._TRANSFORMER, 'A fitted transformer.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Transformation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterPickleFile(self.P_TRANSFORMER, self._TRANSFORMER)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        try:
            TransformerDump.fromDict(Utils.pickleLoad(self.parameterAsFile(parameters, self.P_TRANSFORMER, context)))
        except TypeError:
            return False, 'Invalid transformer file.'
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        dump = self.parameterAsTransformerDump(parameters, self.P_TRANSFORMER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        maximumMemoryUsage = gdal.GetCacheMax()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)

            # derive band count
            X0 = np.ones((1, reader.bandCount()), np.float32)
            Xt0 = dump.transformer.inverse_transform(X0)
            bandCount = Xt0.shape[1]

            # init result raster
            noDataValue = Utils.defaultNoDataValue(np.float32)
            writer = Driver(filename, feedback=feedback).createLike(reader, Qgis.Float32, bandCount)
            lineMemoryUsage = reader.lineMemoryUsage() + reader.lineMemoryUsage(bandCount, 4)
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
                arrayX = reader.arrayFromBlock(block)
                valid = np.all(reader.maskArray(arrayX), axis=0)
                X = list()
                for a in arrayX:
                    X.append(a[valid])
                Xt = dump.transformer.inverse_transform(np.transpose(X))
                arrayXt = np.full((bandCount, *valid.shape), noDataValue, np.float32)
                for i, aXt in enumerate(arrayXt):
                    aXt[valid] = Xt[:, i]
                    writer.writeArray2d(aXt, i + 1, xOffset=block.xOffset, yOffset=block.yOffset)

            writer.setNoDataValue(noDataValue)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
