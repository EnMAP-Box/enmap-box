from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np
from osgeo import gdal

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsVectorLayer, QgsRasterLayer, Qgis,
                       QgsProcessingException)
from typeguard import typechecked


@typechecked
class CreateRgbImageFromClassProbabilityAlgorithm(EnMAPProcessingAlgorithm):
    P_PROBABILITY, _PROBABILITY = 'probability', 'Class probability/fraction layer'
    P_COLORS, _COLORS = 'colors', 'Colors'
    P_COLORS_LAYER, _COLORS_LAYER = 'colorsLayer', 'Colors from categorized layer'
    P_OUTPUT_RGB, _OUTPUT_RGB = 'outputRGBImage', 'Output RGB image'

    def displayName(self):
        return 'Create RGB image from class probability/fraction layer'

    def shortDescription(self):
        return 'Create an RGB image from a class fraction layer or class probability layer.' \
               'The RGB pixel color of a single pixel is given by the weighted mean of the given category colors.' \
               'The weights are given by class fractions/probabilities (i.e. values between 0 and 1).' \
               '\nFor example, pure pixels with cover fractions of 1 appear in its pure category color. ' \
               'A mixed-pixel with a 50% fractions in two categories colored in red and green,' \
               'appears in a dull yellow ( 0.5 x (255, 0, 0) + 0.5 x (0, 255, 0) = (127, 127, 0) ).'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._PROBABILITY, 'A class fraction layer or class probability layer used as weights for calculating '
                                'final pixel colors.'),
            (self._COLORS,
             "Comma separated list of hex-color strings (e.g. '#FF0000' for red) representing (pure) category colors, "
             'one color for each band in the given class probability/fraction layer. '
             'If not specified, colors have to be specified by a categorized layer (Colors from categorized layer).'),
            (self._COLORS_LAYER, 'A categorized layer with (pure) category colors, '
                                 'one category for each band in the given class probability/fraction layer. '
                                 'If not specified, colors have to be specified by list (Colors).'),
            (self._OUTPUT_RGB, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterConversion.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_PROBABILITY, self._PROBABILITY)
        self.addParameterString(self.P_COLORS, self._COLORS, None, False, True, False)
        self.addParameterMapLayer(self.P_COLORS_LAYER, self._COLORS_LAYER, None, True, False)
        self.addParameterRasterDestination(self.P_OUTPUT_RGB, self._OUTPUT_RGB)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        probability = self.parameterAsRasterLayer(parameters, self.P_PROBABILITY, context)
        styledLayer = self.parameterAsLayer(parameters, self.P_COLORS_LAYER, context)
        colors = self.parameterAsValues(parameters, self.P_COLORS, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RGB, context)
        maximumMemoryUsage = gdal.GetCacheMax()

        categories = None
        if colors is not None:
            categories = [Category(value, str(value), color) for value, color in enumerate(colors, 1)]
        if isinstance(styledLayer, QgsVectorLayer):
            categories = Utils.categoriesFromCategorizedSymbolRenderer(styledLayer.renderer())
        if isinstance(styledLayer, QgsRasterLayer):
            categories = Utils.categoriesFromPalettedRasterRenderer(styledLayer.renderer())
        if categories is None:
            raise QgsProcessingException('Category colors not specified.')
        if probability.bandCount() != len(categories):
            raise QgsProcessingException(
                f'Number of bands ({probability.bandCount()}) '
                f'not matching number of category colors ({len(categories)})'
            )

        reader = RasterReader(probability)
        driver = Driver(filename, feedback=feedback)
        writer = driver.createLike(reader, Qgis.Byte, 3)
        lineMemoryUsage = reader.lineMemoryUsage()
        lineMemoryUsage += reader.lineMemoryUsage(3, Qgis.Float32)
        blockSizeY = min(reader.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
        blockSizeX = reader.width()
        for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
            arrayRgb = np.zeros((3, block.height, block.width), np.float32)
            for bandNo, category in enumerate(categories, 1):
                arrayScore = np.clip(reader.arrayFromBlock(block, [bandNo])[0], 0, 1)
                np.clip(reader.arrayFromBlock(block, [bandNo])[0], 0, 1, arrayScore)
                color = QColor(category.color)
                rgb = [color.red(), color.green(), color.blue()]
                for a, v in zip(arrayRgb, rgb):
                    a[:] += arrayScore * v
            writer.writeArray(arrayRgb, block.xOffset, block.yOffset)

        return {self.P_OUTPUT_RGB: filename}
