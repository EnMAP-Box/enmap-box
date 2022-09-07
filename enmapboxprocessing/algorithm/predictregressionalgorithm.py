from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis, QgsProcessingException)
from typeguard import typechecked


@typechecked
class PredictRegressionAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_REGRESSOR, _REGRESSOR = 'regressor', 'Regressor'
    P_OUTPUT_REGRESSION, _OUTPUT_REGRESSION = 'outputRegression', 'Output regression layer'

    def displayName(self) -> str:
        return 'Predict regression layer'

    def shortDescription(self) -> str:
        return 'Uses a fitted regressor to predict a regression layer from a raster layer with features.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer with bands used as features. '
                           'Regressor features and raster bands are matched by name.'),
            (self._REGRESSOR, 'A fitted regressor.'),
            (self._OUTPUT_REGRESSION, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Regression.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterPickleFile(self.P_REGRESSOR, self._REGRESSOR)
        self.addParameterRasterDestination(self.P_OUTPUT_REGRESSION, self._OUTPUT_REGRESSION)

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        try:
            dump = RegressorDump.fromDict(
                Utils.pickleLoad(self.parameterAsFile(parameters, self.P_REGRESSOR, context))
            )
        except TypeError:
            return False, 'Invalid regressor file.'
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        dump = self.parameterAsRegressorDump(parameters, self.P_REGRESSOR, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_REGRESSION, context)
        maximumMemoryUsage = Utils.maximumMemoryUsage()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            rasterReader = RasterReader(raster)
            bandNames = [rasterReader.bandName(i + 1) for i in range(rasterReader.bandCount())]

            # match regressor features with raster band names
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

            nBands = len(dump.targets)
            writer = Driver(filename, feedback=feedback).createLike(rasterReader, Qgis.DataType.Float32, nBands)
            noDataValue = Utils.defaultNoDataValue(np.float32)
            lineMemoryUsage = rasterReader.lineMemoryUsage() + rasterReader.lineMemoryUsage(nBands, 4)
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in rasterReader.walkGrid(blockSizeX, blockSizeY, feedback):
                arrayX = rasterReader.arrayFromBlock(block, bandList)
                valid = np.all(rasterReader.maskArray(arrayX, bandList), axis=0)
                X = list()
                for a in arrayX:
                    X.append(a[valid])
                y = dump.regressor.predict(np.transpose(X))
                if y.ndim == 1:
                    y = y.reshape((-1, 1))
                arrayY = np.full((nBands, *valid.shape), noDataValue, np.float32)
                for i, aY in enumerate(arrayY):
                    aY[valid] = y[:, i]
                    writer.writeArray2d(aY, i + 1, xOffset=block.xOffset, yOffset=block.yOffset)

            for bandNo, t in enumerate(dump.targets, 1):
                writer.setBandName(t.name, bandNo)
                if t.color is not None:
                    writer.setBandColor(QColor(t.color), bandNo)
            writer.setNoDataValue(noDataValue)

            result = {self.P_OUTPUT_REGRESSION: filename}
            self.toc(feedback, result)

        return result
