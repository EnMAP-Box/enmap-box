from typing import Dict, Any, List, Tuple

import numpy as np

import processing
from enmapboxprocessing.algorithm.creategridalgorithm import CreateGridAlgorithm
from enmapboxprocessing.algorithm.rasterizecategorizedvectoralgorithm import RasterizeCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.translatecategorizedrasteralgorithm import TranslateCategorizedRasterAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.numpyutils import NumpyUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsVectorLayer
from enmapbox.typeguard import typechecked


@typechecked
class ClassFractionFromCategorizedLayerAlgorithm(EnMAPProcessingAlgorithm):
    P_CATEGORIZED_LAYER, _CATEGORIZED_LAYER = 'categorizedLayer', 'Categorized layer'
    P_GRID, _GRID = 'grid', 'Grid'
    P_COVERAGE, _COVERAGE = 'coverage', 'Minimum pixel coverage [%]'
    P_OUTPUT_FRACTION_RASTER, _OUTPUT_FRACTION_RASTER = 'outputFraction', 'Output class fraction layer'

    def displayName(self):
        return 'Class fraction layer from categorized layer'

    def shortDescription(self):
        return 'Rasterize/resample a categorized vector/raster layer into class fractions. ' \
               'Categories are rasterized/resampled at/to a x10 finer resolution ' \
               'and aggregated to class-wise fractions at destination resolution. ' \
               'This approach leads to fractions that are accurate to the percent.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CATEGORIZED_LAYER, 'A categorized layer to be rasterized/resampled.'),
            (self._GRID, 'The target grid.'),
            (self._COVERAGE, 'Exclude all pixel where coverage is smaller than given threshold.'),
            (self._OUTPUT_FRACTION_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterMapLayer(self.P_CATEGORIZED_LAYER, self._CATEGORIZED_LAYER)
        self.addParameterRasterLayer(self.P_GRID, self._GRID)
        self.addParameterInt(self.P_COVERAGE, self._COVERAGE, 0, False, 0, 100, advanced=True)
        self.addParameterRasterDestination(self.P_OUTPUT_FRACTION_RASTER, self._OUTPUT_FRACTION_RASTER)

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        layer = self.parameterAsLayer(parameters, self.P_CATEGORIZED_LAYER, context)
        if isinstance(layer, QgsVectorLayer):
            return self.checkParameterVectorClassification(parameters, self.P_CATEGORIZED_LAYER, context)
        elif isinstance(layer, QgsRasterLayer):
            return self.checkParameterRasterClassification(parameters, self.P_CATEGORIZED_LAYER, context)
        else:
            raise ValueError

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        layer = self.parameterAsLayer(parameters, self.P_CATEGORIZED_LAYER, context)
        grid = self.parameterAsRasterLayer(parameters, self.P_GRID, context)
        minCoverage = self.parameterAsInt(parameters, self.P_COVERAGE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_FRACTION_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # create x10 grid
            alg = CreateGridAlgorithm()
            parameters = {
                alg.P_CRS: grid.crs(),
                alg.P_EXTENT: grid.extent(),
                alg.P_WIDTH: grid.width() * 10,
                alg.P_HEIGHT: grid.height() * 10,
                alg.P_UNIT: alg.PixelUnits,
                alg.P_OUTPUT_GRID: Utils.tmpFilename(filename, 'grid.x10.vrt')
            }
            gridX10 = processing.run(alg, parameters, None, feedback2, context, True)[alg.P_OUTPUT_GRID]

            if isinstance(layer, QgsVectorLayer):
                # burn classes at x10 grid
                feedback.pushInfo('Burn classes at x10 finer resolution')
                alg = RasterizeCategorizedVectorAlgorithm()
                parameters = {
                    alg.P_CATEGORIZED_VECTOR: layer,
                    alg.P_GRID: gridX10,
                    alg.P_COVERAGE: 0,
                    alg.P_MAJORITY_VOTING: False,
                    alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'classification.x10.tif')
                }
                processing.run(alg, parameters, None, feedback2, context, True)
                classificationX10 = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])
            elif isinstance(layer, QgsRasterLayer):
                # burn classes at x10 grid
                feedback.pushInfo('Burn classes at x10 finer resolution')
                alg = TranslateCategorizedRasterAlgorithm()
                parameters = {
                    alg.P_CATEGORIZED_RASTER: layer,
                    alg.P_GRID: gridX10,
                    alg.P_MAJORITY_VOTING: False,
                    alg.P_OUTPUT_CATEGORIZED_RASTER: Utils.tmpFilename(filename, 'classification.x10.tif')
                }
                processing.run(alg, parameters, None, feedback2, context, True)
                classificationX10 = QgsRasterLayer(parameters[alg.P_OUTPUT_CATEGORIZED_RASTER])
            else:
                raise ValueError()

            categories = Utils.categoriesFromRenderer(classificationX10.renderer())

            # derive fractions (in percentage) at final grid
            reader = RasterReader(classificationX10)
            classArrayX10 = reader.array()[0]
            mask = np.full((grid.height(), grid.width()), False, bool)
            fractionArrays = list()
            for category in categories:
                categoryMaskX10 = classArrayX10 == category.value
                fractionArray = NumpyUtils.rebinSum(categoryMaskX10, mask.shape).astype(np.uint8)
                categoryMask = fractionArray > 0
                np.logical_or(mask, categoryMask, out=mask)
                fractionArrays.append(fractionArray)

            minCoverMask = np.sum(fractionArrays, 0) >= minCoverage
            np.logical_and(mask, minCoverMask, out=mask)
            invalid = ~mask
            noDataValue = 255
            for fractionArray in fractionArrays:
                fractionArray[invalid] = noDataValue

            # write
            driver = Driver(filename, feedback=feedback)
            writer = driver.createFromArray(fractionArrays, grid.extent(), grid.crs())
            writer.setNoDataValue(noDataValue)
            for bandNo, category in enumerate(categories, 1):
                writer.setBandName(category.name, bandNo)
                writer.setMetadataItem('color', category.color, '', bandNo)
                writer.setScale(1 / 100, bandNo)
            writer.close()
            result = {self.P_OUTPUT_FRACTION_RASTER: filename}
            self.toc(feedback, result)

        return result
