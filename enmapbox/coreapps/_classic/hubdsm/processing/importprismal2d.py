from _classic.hubdsm.algorithm.importprismal2d import importPrismaL2D
from _classic.hubdsm.processing.enmapalgorithm import *


class ImportPrismaL2D(EnMAPAlgorithm):
    def displayName(self):
        return 'Import PRISMA L2D Product'

    def description(self):
        return importPrismaL2D.__doc__

    def group(self):
        return Group.ImportData.value

    P_FILE = 'file'
    P_OUTRASTER = 'outraster'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterFile(
                name=self.P_FILE, description='HE5 File',
                help=Help(text='HE5 file associated with L2D product.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER, description='Output Raster', defaultValue='PRISMA_L2D_SPECTRAL.tif'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        ds = importPrismaL2D(
            filenameHe5=self.parameter(parameters, self.P_FILE, context),
            filenameSpectral=self.parameter(parameters, self.P_OUTRASTER, context),
        )
        return {self.P_OUTRASTER: ds.GetDescription()}
