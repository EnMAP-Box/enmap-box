from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.creategridalgorithm import CreateGridAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.utils import Utils
from processing.core.Processing import Processing
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer)
from typeguard import typechecked


@typechecked
class TranslateCategorizedRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_CATEGORIZED_RASTER, _CATEGORIZED_RASTER = 'categorizedRaster', 'Categorized raster layer'
    P_GRID, _GRID = 'grid', 'Grid'
    P_MAJORITY_VOTING, _MAJORITY_VOTING = 'majorityVoting', 'Majority voting'
    P_OUTPUT_CATEGORIZED_RASTER, _OUTPUT_CATEGORIZED_RASTER = 'outputTranslatedCategorizedRaster', \
                                                              'Output categorized raster layer'

    def displayName(self):
        return 'Translate categorized raster layer'

    def shortDescription(self):
        return 'Translates categorized raster layer into target grid.\n' \
               'Resampling is done via a two-step majority voting approach. ' \
               'First, the categorized raster layer is resampled at x10 finer resolution, ' \
               'and subsequently aggregated back to the target resolution using majority voting. ' \
               'This approach leads to pixel-wise class decisions that are accurate to the percent.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CATEGORIZED_RASTER, 'A categorized raster layer to be resampled.'),
            (self._GRID, 'The target grid.'),
            (self._MAJORITY_VOTING, 'Whether to use majority voting. '
                                    'Turn off to use simple nearest neighbour resampling, which is much faster, '
                                    'but may result in highly inaccurate decisions.'),
            (self._OUTPUT_CATEGORIZED_RASTER, self.RasterFileDestination)
        ]

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        return self.checkParameterRasterClassification(parameters, self.P_CATEGORIZED_RASTER, context)

    def group(self):
        return Group.Test.value + Group.RasterConversion.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_CATEGORIZED_RASTER, self._CATEGORIZED_RASTER)
        self.addParameterRasterLayer(self.P_GRID, self._GRID)
        self.addParameterBoolean(self.P_MAJORITY_VOTING, self._MAJORITY_VOTING, True, False, advanced=True)
        self.addParameterRasterDestination(
            self.P_OUTPUT_CATEGORIZED_RASTER, self._OUTPUT_CATEGORIZED_RASTER, allowVrt=True)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classification = self.parameterAsRasterLayer(parameters, self.P_CATEGORIZED_RASTER, context)
        grid = self.parameterAsRasterLayer(parameters, self.P_GRID, context)
        majorityVoting = self.parameterAsBoolean(parameters, self.P_MAJORITY_VOTING, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_CATEGORIZED_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            isGridMatching = all([grid.crs() == classification.crs(),
                                  grid.extent() == classification.extent(),
                                  grid.width() == classification.width(),
                                  grid.height() == classification.height()])
            if isGridMatching or majorityVoting is False:
                # use simple nn-resampling
                alg = TranslateRasterAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_RASTER: classification,
                    alg.P_GRID: grid,
                    alg.P_RESAMPLE_ALG: self.NearestNeighbourResampleAlg,
                    alg.P_COPY_STYLE: True,
                    alg.P_OUTPUT_RASTER: filename
                }
                Processing.runAlgorithm(alg, parameters, None, feedback2, context)
            else:
                # create oversampling grid
                alg = CreateGridAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_CRS: grid.crs(),
                    alg.P_EXTENT: grid.extent(),
                    alg.P_UNIT: alg.PixelUnits,
                    alg.P_WIDTH: grid.width() * 10,
                    alg.P_HEIGHT: grid.height() * 10,
                    alg.P_OUTPUT_GRID: Utils.tmpFilename(filename, 'grid.x10.vrt')
                }
                result = Processing.runAlgorithm(alg, parameters, None, feedback2, context)
                oversamplingGrid = QgsRasterLayer(result[alg.P_OUTPUT_GRID])

                # translate into oversampling grid
                alg = TranslateRasterAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_RASTER: classification,
                    alg.P_GRID: oversamplingGrid,
                    alg.P_RESAMPLE_ALG: alg.NearestNeighbourResampleAlg,
                    alg.P_COPY_STYLE: True,
                    alg.P_OUTPUT_RASTER: Utils.tmpFilename(filename, 'classification.x10.vrt')
                }
                result = Processing.runAlgorithm(alg, parameters, None, feedback2, context)
                oversamplingClassification = QgsRasterLayer(result[alg.P_OUTPUT_RASTER])

                # final majority voting
                alg = TranslateRasterAlgorithm()
                alg.initAlgorithm()
                parameters = {
                    alg.P_RASTER: oversamplingClassification,
                    alg.P_GRID: grid,
                    alg.P_RESAMPLE_ALG: alg.ModeResampleAlg,
                    alg.P_COPY_STYLE: True,
                    alg.P_OUTPUT_RASTER: filename
                }
                Processing.runAlgorithm(alg, parameters, None, feedback2, context)

            result = {self.P_OUTPUT_CATEGORIZED_RASTER: filename}
            self.toc(feedback, result)
        return result
