from _classic.hubdsm.algorithm.importenmapl1c import importEnmapL1C
from _classic.hubdsm.processing.enmapalgorithm import *


class ImportEnmapL1C(EnMAPAlgorithm):
    def displayName(self):
        return 'Import EnMAP L1C Product'

    def description(self):
        return importEnmapL1C.__doc__

    def group(self):
        return Group.ImportData.value

    P_FILE = 'file'
    P_OUTRASTER = 'outraster'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterFile(
                name=self.P_FILE, description='METADATA.XML',
                help=Help(text='Metadata file associated with L1C product.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER, description='Output VRT', defaultValue='EnMAP_L1C_SPECTRAL.vrt'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        ds = importEnmapL1C(
            filenameMetadataXml=self.parameter(parameters, self.P_FILE, context),
            filenameSpectral=self.parameter(parameters, self.P_OUTRASTER, context),
        )
        return {self.P_OUTRASTER: ds.GetDescription()}
