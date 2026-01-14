from collections import OrderedDict

import numpy as np

from _classic.hubdsm.algorithm.aggregatebands import aggregateBands
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.processing.enmapalgorithm import *


class AggregateBands(EnMAPAlgorithm):
    def displayName(self):
        return 'Aggregate Raster Bands'

    def description(self):
        return 'Aggregate multiband raster into singleband raster.'

    def group(self):
        return Group.Auxilliary.value

    P_RASTER = 'raster'
    P_FUNCTION = 'function'
    P_OUTPUT_RASTER = 'outraster'

    FUNCTIONS = OrderedDict(
        min=np.min,
        max=np.max,
        mean=np.mean,
        median=np.median,
        sum=np.sum,
        product=np.product,
        any=np.any,
        all=np.all
    )

    def defineCharacteristics(self):

        self.addParameter(
            EnMAPProcessingParameterRasterLayer(
                name=self.P_RASTER, description='Raster')
        )

        self.addParameter(
            EnMAPProcessingParameterEnum(
                name=self.P_FUNCTION, description='Aggregation function', options=list(self.FUNCTIONS.keys()))
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTPUT_RASTER, description='Output Raster'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        qgsRasterLayer: QgsRasterLayer = self.parameter(parameters, self.P_RASTER, context)
        raster = Raster.open(qgsRasterLayer.source())
        aggregationFunctionSelection = self.parameter(parameters, self.P_FUNCTION, context)
        aggregationFunction = list(self.FUNCTIONS.values())[aggregationFunctionSelection]
        filename = self.parameter(parameters, self.P_OUTPUT_RASTER, context)
        outraster = aggregateBands(raster=raster, aggregationFunction=aggregationFunction, filename=filename)
        return {self.P_OUTPUT_RASTER: filename}
