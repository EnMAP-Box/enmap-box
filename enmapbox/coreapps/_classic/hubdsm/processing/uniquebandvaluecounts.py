from _classic.hubdsm.processing.enmapalgorithm import *
from _classic.hubdsm.algorithm.uniquebandvaluecounts import uniqueBandValueCounts
from _classic.hubdsm.core.raster import Raster


class UniqueBandValueCounts(EnMAPAlgorithm):
    def displayName(self):
        return 'Unique Band Value Counts'

    def description(self):
        return uniqueBandValueCounts.__doc__

    def group(self):
        return Group.Auxilliary.value

    P_RASTER = 'raster'
    P_BAND = 'band'
    P_OUTSTRING = 'outstring'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterRasterLayer(
                name=self.P_RASTER, description='Raster')
        )

        self.addParameter(
            EnMAPProcessingParameterBand(
                name=self.P_BAND, description='Band', parentLayerParameterName=self.P_RASTER, defaultValue=1
            )
        )

        self.addOutput(
            EnMAPProcessingOutputString(
                name=self.P_OUTSTRING, description='Output String', help=Help(text='Output string.')))

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        qgsRasterLayer: QgsRasterLayer = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        raster = Raster.open(qgsRasterLayer.source())
        band = raster.band(number=self.parameterAsInt(parameters, self.P_BAND, context))
        total = 0
        text = list()
        for id, count in uniqueBandValueCounts(band=band).items():
            text.append(f'{id}: {count}')
            total += count
        text.append(f'total: {total}')
        text = '\n'.join(text)
        feedback.pushInfo(text)
        return {self.P_OUTSTRING: text}
