from _classic.hubdsm.algorithm.importenmapl2a import importEnmapL2A
from _classic.hubdsm.algorithm.saveasenvi import saveAsEnvi
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.processing.enmapalgorithm import *


class SaveAsEnvi(EnMAPAlgorithm):
    def displayName(self):
        return 'Save as ENVI Raster'

    def description(self):
        return saveAsEnvi.__doc__

    def group(self):
        return Group.Auxilliary.value

    P_RASTER = 'raster'
    P_OUTRASTER = 'outraster'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterRasterLayer(
                name=self.P_RASTER, description='Raster'
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER, description='Output Raster'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        qgsRasterLayer = self.parameter(parameters, self.P_RASTER, context)
        assert isinstance(qgsRasterLayer, QgsRasterLayer)
        gdalRaster = GdalRaster.open(qgsRasterLayer.source())
        outGdalRaster = saveAsEnvi(
            gdalRaster=gdalRaster,
            filename=self.parameter(parameters, self.P_OUTRASTER, context),
        )
        return {self.P_OUTRASTER: outGdalRaster.filename}
