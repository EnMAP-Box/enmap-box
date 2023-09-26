from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsMapLayer


@typechecked
class ClassificationFromRenderedImageAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_OUTPUT_CLASSIFICATION, _OUTPUT_CLASSIFICATION = 'outputClassification', 'Output classification layer'

    @classmethod
    def displayName(cls) -> str:
        return 'Classification layer from rendered image'

    def shortDescription(self) -> str:
        return 'Creates classification layer from a rendered image. ' \
               'Classes are derived from the unique renderer RGBA values.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'The raster layer to be classified.'),
            (self._OUTPUT_CLASSIFICATION, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterRasterDestination(self.P_OUTPUT_CLASSIFICATION, self._OUTPUT_CLASSIFICATION)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_CLASSIFICATION, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)
            feedback.pushInfo(f'Raster renderer: {raster.renderer()}')
            block = raster.renderer().block(1, raster.extent(), raster.width(), raster.height())
            array = Utils().qgsRasterBlockToNumpyArray(block)
            values = np.unique(array)
            feedback.pushInfo(f'Number of unique classes: {len(values)}')
            aValues = np.bitwise_and(values >> 24, 255)
            rValues = np.bitwise_and(values >> 16, 255)
            gValues = np.bitwise_and(values >> 8, 255)
            bValues = np.bitwise_and(values, 255)
            categories = list()
            for a, r, g, b, v in zip(aValues, rValues, gValues, bValues, values):
                if a == 0:
                    array[array == v] = 0
                    continue
                name = color = QColor(r, g, b).name()
                categories.append(Category(int(v), name, color))

            writer = Driver(filename).createFromArray([array], raster.extent(), raster.crs())
            writer.setNoDataValue(0)
            writer.setBandName('classification from rgb image', 1)
            del writer

            layer = QgsRasterLayer(filename)
            renderer = Utils().palettedRasterRendererFromCategories(layer.dataProvider(), 1, categories)
            layer.setRenderer(renderer)
            layer.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {self.P_OUTPUT_CLASSIFICATION: filename}
            self.toc(feedback, result)

        return result
