from random import randint
from typing import Dict, Any, List, Tuple

import numpy as np

import processing
from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.randompointsfromcategorizedrasteralgorithm import \
    RandomPointsFromCategorizedRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.typing import Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsMapLayer, QgsRasterLayer, QgsProcessingException


@typechecked
class RandomPointsFromRasterAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_BAND, _BAND = 'band', 'Band'
    P_N, _N = 'n', 'Number of points per value-range'
    P_BOUNDARIES, _BOUNDARIES = 'boundaries', 'Range boundaries'
    O_BOUNDARIES = ['min < value <= max', 'min <= value < max', 'min <= value <= max', 'min < value < max']
    LeftOpenBoundary, RightOpenBoundary, ClosedBoundary, OpenBoundary = range(len(O_BOUNDARIES))
    P_DISTANCE_GLOBAL, _DISTANCE_GLOBAL = 'distanceGlobal', \
                                          'Minimum distance between points (in meters)'
    P_DISTANCE_STRATUM, _DISTANCE_STRATUM = 'distanceStatum', \
                                            'Minimum distance between points inside category (in meters)'
    P_SEED, _SEED = 'seed', 'Random seed'
    P_OUTPUT_POINTS, _OUTPUT_POINTS = 'outputPoints', 'Output point layer'

    @classmethod
    def displayName(cls) -> str:
        return 'Random points from raster layer value-ranges'

    def shortDescription(self) -> str:
        return 'This algorithm creates a new point layer with a given number of random points, ' \
               'all of them within specified value-ranges of the given raster band.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A raster layer.'),
            (self._BAND, 'The band to draw points from. If not selected, the first renderer band is used.'),
            (self._N, 'Number of points N to draw from value-range Minimum to Maximum.'
                      'Value-ranges can be specified by actual values (e.g. 42) '
                      'or by percentiles (e.g. p0, p50, p100, etc.).'),
            (self._BOUNDARIES,
             'The boundary type used for all value-ranges.'),
            (self._DISTANCE_GLOBAL,
             'A minimum (Euclidean) distance between points can be specified.'),
            (self._DISTANCE_STRATUM,
             'A minimum (Euclidean) distance between points in a value-range can be specified.'),
            (self._SEED, 'The seed for the random generator can be provided.'),
            (self._OUTPUT_POINTS, self.VectorFileDestination)
        ]

    def group(self):
        return Group.VectorCreation.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBand(self.P_BAND, self._BAND, None, self.P_RASTER, True)
        self.addParameterMatrix(self.P_N, self._N, 0, False, ['Minimum', 'Maximum', '#Points'])
        self.addParameterEnum(self.P_BOUNDARIES, self._BOUNDARIES, self.O_BOUNDARIES, False, self.LeftOpenBoundary)
        self.addParameterInt(self.P_DISTANCE_GLOBAL, self._DISTANCE_GLOBAL, 0, False, 0)
        self.addParameterInt(self.P_DISTANCE_STRATUM, self._DISTANCE_STRATUM, 0, False, 0)
        self.addParameterInt(self.P_SEED, self._SEED, None, True, 1)
        self.addParameterVectorDestination(self.P_OUTPUT_POINTS, self._OUTPUT_POINTS)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        layer = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        bandNo = self.parameterAsBand(parameters, self.P_BAND, context)
        N = self.parameterAsMatrix(parameters, self.P_N, context)
        if N is None:
            raise QgsProcessingException(f'Missing parameter: {self._N}')
        N = np.reshape(N, (-1, 3))
        boundaries = self.parameterAsEnum(parameters, self.P_BOUNDARIES, context)
        distanceGlobal = self.parameterAsInt(parameters, self.P_DISTANCE_GLOBAL, context)
        distanceStratum = self.parameterAsInt(parameters, self.P_DISTANCE_STRATUM, context)
        seed = self.parameterAsInt(parameters, self.P_SEED, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_POINTS, context)

        if bandNo is None:
            bandNo = layer.renderer().usesBands()[0]

        if seed is not None:
            np.random.seed(seed)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # create stratification
            N2 = N.copy()
            samplesPerStrata = list()
            categories = list()
            for stratumNo, row in enumerate(N2, 1):
                samplesPerStrata.append(int(row[-1]))
                row[-1] = stratumNo
                stratumName = self.O_BOUNDARIES[boundaries].replace('min', str(row[0])).replace('max', str(row[1]))
                stratumColor = QColor(randint(0, 2 ** 24)).name()
                categories.append(Category(stratumNo, stratumName, stratumColor))
            N2 = N2.flatten().tolist()
            alg2 = 'native:reclassifybytable'
            parameters2 = {
                'INPUT_RASTER': layer,
                'RASTER_BAND': bandNo,
                'TABLE': N2,
                'NO_DATA': 0,
                'RANGE_BOUNDARIES': boundaries,
                'NODATA_FOR_MISSING': True,
                'DATA_TYPE': 2,  # uint16
                'OUTPUT': Utils().tmpFilename(filename, 'stratification.tif')
            }
            processing.run(alg2, parameters2, None, feedback2, context, True)
            stratification = QgsRasterLayer(parameters2['OUTPUT'])
            renderer = Utils().palettedRasterRendererFromCategories(stratification.dataProvider(), 1, categories)
            stratification.setRenderer(renderer)
            stratification.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            # draw from stratification
            alg3 = RandomPointsFromCategorizedRasterAlgorithm()
            alg3.initAlgorithm()
            parameters3 = {
                alg3.P_STRATIFICATION: stratification,
                alg3.P_N: samplesPerStrata,
                alg3.P_SEED: seed,
                alg3.P_DISTANCE_GLOBAL: distanceGlobal,
                alg3.P_DISTANCE_STRATUM: distanceStratum,
                alg3.P_OUTPUT_POINTS: filename
            }
            processing.run(alg3, parameters3, None, feedback, context, True)

            result = {self.P_OUTPUT_POINTS: filename}
            self.toc(feedback, result)
        return result
