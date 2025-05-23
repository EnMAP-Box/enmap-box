from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis, QgsProcessingException)


@typechecked
class TransformRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_TRANSFORMER, _TRANSFORMER = 'transformer', 'Transformer'
    P_MATCH_BY_NAME, _MATCH_BY_NAME = 'matchByName', 'Match features and bands by name'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Transform raster layer'

    def shortDescription(self) -> str:
        return 'Uses a fitted transformer to transform a raster layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'The raster layer to be transformed. '
                           'Transformer features and raster bands are matched by name.'),
            (self._TRANSFORMER, 'A fitted transformer.'),
            (self._MATCH_BY_NAME, 'Whether to match raster bands and regressor features by name.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Transformation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterPickleFile(self.P_TRANSFORMER, self._TRANSFORMER)
        self.addParameterBoolean(self.P_MATCH_BY_NAME, self._MATCH_BY_NAME, False, True)
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
        matchByName = self.parameterAsBoolean(parameters, self.P_MATCH_BY_NAME, context)
        format, options = self.GTiffFormat, self.DefaultGTiffCreationOptions
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        maximumMemoryUsage = gdal.GetCacheMax()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)
            bandNames = [reader.bandName(i + 1) for i in range(reader.bandCount())]

            # match transformer features with raster band names
            # match regressor features with raster band names
            bandList = None
            if matchByName:
                try:  # try to find matching bands ...
                    bandList = [bandNames.index(feature) + 1 for feature in dump.features]
                except ValueError:
                    bandList = None

            # ... if not possible, try to remove bad bands
            if bandList is None and len(bandNames) != len(dump.features):
                goodBandList = [bandNo for bandNo in reader.bandNumbers()
                                if reader.badBandMultiplier(bandNo) == 1]
                if len(goodBandList) == len(dump.features):
                    bandList = goodBandList

            # ... if not possible, use original bands, if overall number of bands and features do match
            if bandList is None and len(bandNames) != len(dump.features):
                message = f'transformer features ({dump.features}) not matching raster bands ({bandNames})\n' \
                          f'number of features: {len(dump.features)}\n' \
                          f'number of bands: {len(bandNames)}\n'
                feedback.reportError(message, fatalError=True)
                raise QgsProcessingException(message)

            if (bandList is not None) and (len(bandList) != raster.bandCount()):
                usedBandNames = [raster.bandName(bandNo) for bandNo in bandList]
                feedback.pushInfo(f'Bands used as features: {", ".join(usedBandNames)}')

            # derive band count
            if bandList is None:
                X0 = np.ones((1, reader.bandCount()), np.float32)
            else:
                X0 = np.ones((1, len(bandList)), np.float32)
            Xt0 = dump.transformer.transform(X0)
            bandCount = Xt0.shape[1]

            # init result raster
            noDataValue = Utils.defaultNoDataValue(np.float32)
            writer = Driver(filename, feedback=feedback).createLike(reader, Qgis.Float32, bandCount)
            lineMemoryUsage = reader.lineMemoryUsage() + reader.lineMemoryUsage(bandCount, 4)
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
                arrayX = reader.arrayFromBlock(block, bandList)
                valid = np.all(reader.maskArray(arrayX, bandList), axis=0)
                X = list()
                for a in arrayX:
                    X.append(a[valid])
                Xt = dump.transformer.transform(np.transpose(X))
                arrayXt = np.full((bandCount, *valid.shape), noDataValue, np.float32)
                for i, aXt in enumerate(arrayXt):
                    aXt[valid] = Xt[:, i]
                    writer.writeArray2d(aXt, i + 1, xOffset=block.xOffset, yOffset=block.yOffset)

            writer.setNoDataValue(noDataValue)
            writer.close()
            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
