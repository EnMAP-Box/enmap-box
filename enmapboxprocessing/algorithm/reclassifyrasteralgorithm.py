from typing import Dict, Any, List, Tuple

import numpy as np

from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.core import QgsRasterLayer, QgsMapLayer
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, Qgis)
from typeguard import typechecked


@typechecked
class ReclassifyRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_MAPPING, _MAPPING = 'mapping', 'Class mapping'
    P_CATEGORIES, _CATEGORIES = 'categories', 'Categories'
    P_NO_DATA_VALUE, _NO_DATA_VALUE = 'noDataValue', 'No data value'
    P_OUTPUT_CLASSIFICATION, _OUTPUT_CLASSIFCATION = 'outputClassification', 'Output classification layer'

    def displayName(self) -> str:
        return 'Reclassify raster layer'

    def shortDescription(self) -> str:
        return 'This algorithm reclassifies a raster by assigning new class values based on a class mapping.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer to be reclassified.'),
            (self._MAPPING, 'A list of source to target class value mappings. '
                            'E.g. to merge source values 1 and 2 into target value 1, '
                            'and source values 3 and 4 into target value 2, '
                            'use {1:1, 2:1, 3:2, 4:2}'),
            (self._CATEGORIES, 'A list of target categories in short notation: '
                               "[(1, 'Class A', '#e60000'), (2, 'Class B', '#267300')]"),
            (self._NO_DATA_VALUE, 'Value used to fill no data regions.'),
            (self._OUTPUT_CLASSIFCATION, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterString(self.P_MAPPING, self._MAPPING)
        self.addParameterString(self.P_CATEGORIES, self._CATEGORIES, optional=True)
        self.addParameterInt(self.P_NO_DATA_VALUE, self._NO_DATA_VALUE, 0, False, advanced=True)
        self.addParameterRasterDestination(self.P_OUTPUT_CLASSIFICATION, self._OUTPUT_CLASSIFCATION)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        mapping = self.parameterAsObject(parameters, self.P_MAPPING, context)
        categories = self.parameterAsObject(parameters, self.P_CATEGORIES, context)
        if categories is not None:
            categories = [Category(*category) for category in categories]
        noDataValue = self.parameterAsInt(parameters, self.P_NO_DATA_VALUE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CLASSIFICATION, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            reader = RasterReader(raster)
            writer = Driver(filename, feedback=feedback).createLike(reader, Qgis.DataType.Int32, reader.bandCount())
            for bandNo in reader.bandNumbers():
                feedback.setProgress(bandNo / reader.bandCount() * 100)

                inarray = reader.array(bandList=[bandNo])[0]
                outarray = np.full_like(inarray, noDataValue, np.int32)

                for v1, v2 in mapping.items():
                    outarray[inarray == v1] = v2

                writer.writeArray2d(outarray, bandNo)

            writer.setNoDataValue(noDataValue)
            writer.close()
            del writer

            if categories is not None:
                layer = QgsRasterLayer(filename)
                renderer = Utils.palettedRasterRendererFromCategories(layer.dataProvider(), 1, categories)
                layer.setRenderer(renderer)
                layer.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {self.P_OUTPUT_CLASSIFICATION: filename}
            self.toc(feedback, result)

        return result
