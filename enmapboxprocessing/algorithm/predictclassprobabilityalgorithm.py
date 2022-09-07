from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis, QgsProcessingException)
from typeguard import typechecked


@typechecked
class PredictClassPropabilityAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_CLASSIFIER, _CLASSIFIER = 'classifier', 'Classifier'
    P_OUTPUT_PROBABILITY, _OUTPUT_PROBABILITY = 'outputProbability', 'Output class probability layer'

    def displayName(self) -> str:
        return 'Predict class probability layer'

    def shortDescription(self) -> str:
        return 'Uses a fitted classifier to predict class probability layer from a raster layer with features.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer with bands used as features. '
                           'Classifier features and raster bands are matched by name.'),
            (self._CLASSIFIER, 'A fitted classifier.'),
            (self._OUTPUT_PROBABILITY, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterPickleFile(self.P_CLASSIFIER, self._CLASSIFIER)
        self.addParameterRasterDestination(self.P_OUTPUT_PROBABILITY, self._OUTPUT_PROBABILITY)

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        try:
            dump = ClassifierDump(**Utils.pickleLoad(self.parameterAsFile(parameters, self.P_CLASSIFIER, context)))
        except TypeError:
            return False, 'Invalid classifier file.'
        if not hasattr(dump.classifier, 'predict_proba'):
            return False, 'Classifier does not support probability predictions.'
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        dump = self.parameterAsClassifierDump(parameters, self.P_CLASSIFIER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_PROBABILITY, context)
        maximumMemoryUsage = gdal.GetCacheMax()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            rasterReader = RasterReader(raster)
            bandNames = [rasterReader.bandName(i + 1) for i in range(rasterReader.bandCount())]

            # match classifier features with raster band names
            try:  # try to find matching bands ...
                bandList = [bandNames.index(feature) + 1 for feature in dump.features]
            except ValueError:
                bandList = None

            # ... if not possible, use original bands, if overall number of bands and features do match
            if bandList is None and len(bandNames) != len(dump.features):
                message = f'classifier features ({dump.features}) not matching raster bands ({bandNames})'
                feedback.reportError(message, fatalError=True)
                raise QgsProcessingException(message)

            if (bandList is not None) and (len(bandList) != raster.bandCount()):
                usedBandNames = [rasterReader.bandName(bandNo) for bandNo in bandList]
                feedback.pushInfo(f'Bands used as features: {", ".join(usedBandNames)}')

            nBands = len(dump.categories)
            dataType = Qgis.DataType.Float32
            gdalDataType = Utils.qgisDataTypeToNumpyDataType(dataType)
            writer = Driver(filename, feedback=feedback).createLike(rasterReader, dataType, nBands)
            lineMemoryUsage = rasterReader.lineMemoryUsage() + rasterReader.lineMemoryUsage(nBands, 32 // 4)
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in rasterReader.walkGrid(blockSizeX, blockSizeY, feedback):
                arrayX = rasterReader.arrayFromBlock(block, bandList)
                valid = np.all(rasterReader.maskArray(arrayX, bandList), axis=0)
                X = list()
                for a in arrayX:
                    X.append(a[valid])
                y = dump.classifier.predict_proba(np.transpose(X))
                arrayY = np.full((nBands, *valid.shape), -1, gdalDataType)
                for i, aY in enumerate(arrayY):
                    aY[valid] = y[:, i]
                    writer.writeArray2d(aY, i + 1, xOffset=block.xOffset, yOffset=block.yOffset)

            for bandNo, c in enumerate(dump.categories, 1):
                writer.setBandName(c.name, bandNo)
            writer.setNoDataValue(-1)

            result = {self.P_OUTPUT_PROBABILITY: filename}
            self.toc(feedback, result)

        return result
