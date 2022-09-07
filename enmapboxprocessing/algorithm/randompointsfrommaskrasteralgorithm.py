from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.randompointsfromcategorizedrasteralgorithm import \
    RandomPointsFromCategorizedRasterAlgorithm
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsMapLayer
from typeguard import typechecked


@typechecked
class RandomPointsFromMaskRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_MASK, _MASK = 'mask', 'Mask raster layer'
    P_N, _N = 'n', 'Number of points'
    P_DISTANCE, _DISTANCE = 'distance', 'Minimum distance between points (in meters)'
    P_SEED, _SEED = 'seed', 'Random seed'
    P_OUTPUT_POINTS, _OUTPUT_POINTS = 'outputPoints', 'Output point layer'

    @classmethod
    def displayName(cls) -> str:
        return 'Random points from mask raster layer'

    def shortDescription(self) -> str:
        return 'This algorithm creates a new point layer with a given number of random points, ' \
               'all of them in the area where the given mask evaluates to true.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._MASK, 'A mask raster layer to draw locations from.'),
            (self._N, 'Number of points to be drawn.'),
            (self._DISTANCE,
             'A minimum distance between points can be specified. A point will not be added if there is an already '
             'generated point within this (Euclidean) distance from the generated location.'),
            (self._SEED, 'The seed for the random generator can be provided.'),
            (self._OUTPUT_POINTS, self.VectorFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.VectorCreation.value

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        return True, ''

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_MASK, self._MASK)
        self.addParameterInt(self.P_N, self._N, None, False, 1)
        self.addParameterInt(self.P_DISTANCE, self._DISTANCE, 0, False, 0)
        self.addParameterInt(self.P_SEED, self._SEED, None, True, 1)
        self.addParameterVectorDestination(self.P_OUTPUT_POINTS, self._OUTPUT_POINTS)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        mask = self.parameterAsRasterLayer(parameters, self.P_MASK, context)
        N = self.parameterAsInts(parameters, self.P_N, context)
        distance = self.parameterAsInt(parameters, self.P_DISTANCE, context)
        seed = self.parameterAsInt(parameters, self.P_SEED, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_POINTS, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # create explicit binary mask and style as classification
            bandList = [mask.renderer().usesBands()[0]]
            reader = RasterReader(mask)
            array = reader.array(bandList=bandList)
            marray = reader.maskArray(array, bandList=bandList, defaultNoDataValue=0.)
            driver = Driver(Utils.tmpFilename(filename, 'mask.tif'), feedback=feedback)
            writer = driver.createFromArray(marray, mask.extent(), mask.crs())
            writer.close()
            stratification = QgsRasterLayer(writer.source())
            categories = [Category(1, 'mask', '#FF0000')]
            renderer = Utils.palettedRasterRendererFromCategories(stratification.dataProvider(), 1, categories)
            stratification.setRenderer(renderer)
            stratification.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            # draw ponts
            alg = RandomPointsFromCategorizedRasterAlgorithm()
            alg.initAlgorithm()
            parameters = {
                alg.P_STRATIFICATION: stratification,
                alg.P_N: N,
                alg.P_DISTANCE_GLOBAL: distance,
                alg.P_SEED: seed,
                alg.P_OUTPUT_POINTS: filename,
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)
            result = {self.P_OUTPUT_POINTS: filename}
            self.toc(feedback, result)
        return result
