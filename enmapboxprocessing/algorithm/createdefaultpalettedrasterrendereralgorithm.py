from typing import Dict, Any, List, Tuple

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsMapLayer)
from typeguard import typechecked


@typechecked
class CreateDefaultPalettedRasterRendererAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_BAND, _BAND = 'band', 'Band'
    P_CATEGORIES, _CATEGORIES = 'categories', 'Categories'

    def displayName(self) -> str:
        return 'Create default paletted raster renderer'

    def shortDescription(self) -> str:
        return 'Create a paletted raster renderer from given categories and set it as the default style of the given raster layer.\n' \
               'This will create/overwrite the QML sidecar file of the given raster layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'The raster layer for which to create the QML sidecar file.'),
            (self._BAND, 'The renderer band.'),
            (self._CATEGORIES, 'Comma separated list of tuples with category value, name and color information. E.g.\n'
                               "(1, 'Urban', '#FF0000'), (2, 'Forest', '#00FF00'), (3, 'Water', '#0000FF')"),
        ]

    def group(self):
        return Group.Test.value + Group.Auxilliary.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBand(self.P_BAND, self._BAND, None, self.P_RASTER)
        self.addParameterString(self.P_CATEGORIES, self._CATEGORIES, None, True)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        band = self.parameterAsInt(parameters, self.P_BAND, context)
        categories = self.parameterAsValues(parameters, self.P_CATEGORIES, context)

        with open(raster.source() + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            try:
                categories = [Category(*category) for category in categories]
            except Exception:
                message = 'Unable to parse categories.'
                feedback.reportError(message, fatalError=True)
                raise QgsProcessingException(message)

            renderer = Utils.palettedRasterRendererFromCategories(raster.dataProvider(), band, categories)
            raster.setRenderer(renderer)
            raster.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {}
            self.toc(feedback, result)

        return result
