from _classic.hubdsm.algorithm.importenmapl2a import importEnmapL2A
from _classic.hubdsm.processing.enmapalgorithm import *


class ImportEnmapL2A(EnMAPAlgorithm):
    def displayName(self):
        return 'Import EnMAP L2A Product'

    def description(self):
        return importEnmapL2A.__doc__

    def group(self):
        return Group.ImportData.value

    P_FILE = 'file'
    P_OUTRASTER = 'outraster'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterFile(
                name=self.P_FILE, description='METADATA.XML',
                help=Help(text='Metadata file associated with L2A product.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER, description='Output VRT', defaultValue='EnMAP_L2A_SPECTRAL.vrt'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        ds = importEnmapL2A(
            filenameMetadataXml=self.parameter(parameters, self.P_FILE, context),
            filenameSpectral=self.parameter(parameters, self.P_OUTRASTER, context),
        )
        return {self.P_OUTRASTER: ds.GetDescription()}
