from math import ceil
from random import randint
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import ClustererDump, Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer,
                       QgsProcessingException, QgsMapLayer)
from typeguard import typechecked


@typechecked
class PredictClusteringAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer with features'
    P_CLUSTERER, _CLUSTERER = 'clusterer', 'Clusterer'
    P_OUTPUT_CLASSIFICATION, _OUTPUT_CLASSIFICATION = 'outputClassification', 'Output classification layer'

    def displayName(self) -> str:
        return 'Predict (unsupervised) classification layer'

    def shortDescription(self) -> str:
        return 'Uses a fitted clusterer to predict an (unsupervised) classification layer from a raster layer with ' \
               'features.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer with bands used as features. '
                           'Clusterer features and raster bands are matched by name to allow for clusterers trained '
                           'on a subset of the raster bands. If raster bands and clusterer features are not matching '
                           'by name, but overall number of bands and features do match, '
                           'raster bands are used in original order.'),
            (self._CLUSTERER, 'A fitted clusterer.'),
            (self._OUTPUT_CLASSIFICATION, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Clustering.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterPickleFile(self.P_CLUSTERER, self._CLUSTERER)
        self.addParameterRasterDestination(self.P_OUTPUT_CLASSIFICATION, self._OUTPUT_CLASSIFICATION)

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        try:
            ClustererDump.fromDict(Utils.pickleLoad(self.parameterAsFile(parameters, self.P_CLUSTERER, context)))
        except TypeError:
            return False, 'Invalid clusterer file.'
        return True, ''

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        dump = self.parameterAsClustererDump(parameters, self.P_CLUSTERER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CLASSIFICATION, context)
        maximumMemoryUsage = Utils.maximumMemoryUsage()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            rasterReader = RasterReader(raster)
            bandNames = [rasterReader.bandName(i + 1) for i in range(rasterReader.bandCount())]

            # match clusterer features with raster band names
            try:  # try to find matching bands ...
                bandList = [bandNames.index(feature) + 1 for feature in dump.features]
            except ValueError:
                bandList = None

            # ... if not possible, use original bands, if overall number of bands and features do match
            if bandList is None and len(bandNames) != len(dump.features):
                message = f'clusterer features ({dump.features}) not matching raster bands ({bandNames})'
                feedback.reportError(message, fatalError=True)
                raise QgsProcessingException(message)

            if (bandList is not None) and (len(bandList) != raster.bandCount()):
                usedBandNames = [rasterReader.bandName(bandNo) for bandNo in bandList]
                feedback.pushInfo(f'Bands used as features: {", ".join(usedBandNames)}')

            # predict
            qgisDataType = Utils.smallesUIntDataType(dump.clusterCount)
            numpyDataType = Utils.qgisDataTypeToNumpyDataType(qgisDataType)
            writer = Driver(filename, feedback=feedback).createLike(rasterReader, qgisDataType, 1)
            noDataValue = 0
            lineMemoryUsage = rasterReader.lineMemoryUsage()
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in rasterReader.walkGrid(blockSizeX, blockSizeY, feedback):
                arrayX = rasterReader.arrayFromBlock(block, bandList)
                valid = np.all(rasterReader.maskArray(arrayX, bandList), axis=0)
                X = list()
                for a in arrayX:
                    X.append(a[valid])
                y = dump.clusterer.predict(np.transpose(X))
                arrayY = np.zeros_like(valid, numpyDataType)
                arrayY[valid] = y + 1  # cluster numbers start with 1!
                writer.writeArray2d(arrayY, 1, xOffset=block.xOffset, yOffset=block.yOffset)
            writer.setNoDataValue(noDataValue)
            del writer

            # create default style
            classification = QgsRasterLayer(filename)
            categories = [Category(i + 1, f'cluster {i + 1}', QColor(randint(0, 2 ** (24) - 1)).name())
                          for i in range(dump.clusterCount)]
            renderer = Utils.palettedRasterRendererFromCategories(classification.dataProvider(), 1, categories)
            classification.setRenderer(renderer)
            classification.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {self.P_OUTPUT_CLASSIFICATION: filename}
            self.toc(feedback, result)

        return result
