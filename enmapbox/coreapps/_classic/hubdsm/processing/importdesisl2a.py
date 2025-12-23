from _classic.hubdsm.algorithm.importdesisl2a import importDesisL2A
from _classic.hubdsm.processing.enmapalgorithm import *


class ImportDesisL2A(EnMAPAlgorithm):
    def displayName(self):
        return 'Import DESIS L2A Product'

    def description(self):
        return importDesisL2A.__doc__

    def group(self):
        return Group.ImportData.value

    P_FILE = 'file'
    P_OUTRASTER = 'outraster'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterFile(
                name=self.P_FILE, description='METADATA.xml',
                help=Help(text='Metadata file associated with L2A product.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER, description='Output VRT', defaultValue='DESIS_L2A_SPECTRAL.vrt'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        ds = importDesisL2A(
            filenameMetadataXml=self.parameter(parameters, self.P_FILE, context),
            filenameSpectral=self.parameter(parameters, self.P_OUTRASTER, context),
        )
        return {self.P_OUTRASTER: ds.GetDescription()}
