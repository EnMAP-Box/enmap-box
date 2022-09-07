from math import ceil
from random import randint
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, Qgis, QgsMapLayer
from typeguard import typechecked


@typechecked
class ClassificationFromClassProbabilityAlgorithm(EnMAPProcessingAlgorithm):
    P_PROBABILITY, _PROBABILITY = 'probability', 'Class probability layer'
    P_OUTPUT_CLASSIFICATION, _OUTPUT_CLASSIFICATION = 'outputClassification', 'Output classification layer'

    @classmethod
    def displayName(cls) -> str:
        return 'Classification layer from class probability/fraction layer'

    def shortDescription(self) -> str:
        return 'Creates classification layer from class probability layer or class fraction layer. ' \
               'Winner class is given by the class with maximum class probabiliy/fraction.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._PROBABILITY, 'A class probability layer or class fraction layer to be classified.'),
            (self._OUTPUT_CLASSIFICATION, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_PROBABILITY, self._PROBABILITY)
        self.addParameterRasterDestination(self.P_OUTPUT_CLASSIFICATION, self._OUTPUT_CLASSIFICATION)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        probability = self.parameterAsRasterLayer(parameters, self.P_PROBABILITY, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_CLASSIFICATION, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            targets = Utils.targetsFromLayer(probability)
            categories = list()
            for bandNo, target in enumerate(targets, 1):
                if target.color is None:
                    color = QColor(randint(0, 255), randint(0, 255), randint(0, 255)).name()
                else:
                    color = target.color
                categories.append(Category(bandNo, target.name, color))

            reader = RasterReader(probability)
            writer = Driver(filename, feedback=feedback).createLike(reader, Qgis.DataType.Byte, 1)
            lineMemoryUsage = reader.lineMemoryUsage()
            blockSizeY = min(probability.height(), ceil(Utils.maximumMemoryUsage() / lineMemoryUsage))
            blockSizeX = probability.width()
            for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
                array = reader.arrayFromBlock(block)
                invalid = ~np.all(reader.maskArray(array), 0)
                array.insert(0, 1. - np.sum(array, 0))  # unclassified fraction
                outarray = np.argmax(array, 0)
                outarray[invalid] = 0
                writer.writeArray2d(outarray, 1, xOffset=block.xOffset, yOffset=block.yOffset)
            writer.setNoDataValue(0)
            writer.close()
            outraster = QgsRasterLayer(filename)
            renderer = Utils.palettedRasterRendererFromCategories(outraster.dataProvider(), 1, categories)
            outraster.setRenderer(renderer)
            outraster.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {self.P_OUTPUT_CLASSIFICATION: filename}
            self.toc(feedback, result)

        return result
