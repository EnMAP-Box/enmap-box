from _classic.hubdsm.algorithm.importenmapl1b import importEnmapL1B
from _classic.hubdsm.processing.enmapalgorithm import *


class ImportEnmapL1B(EnMAPAlgorithm):
    def displayName(self):
        return 'Import EnMAP L1B Product'

    def description(self):
        return importEnmapL1B.__doc__

    def group(self):
        return Group.ImportData.value

    P_FILE = 'file'
    P_OUTRASTER_VNIR = 'outvnir'
    P_OUTRASTER_SWIR = 'outswir'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterFile(
                name=self.P_FILE, description='METADATA.XML',
                fileFilter='*metadata.xml',
                help=Help(text='Metadata file associated with L1B product.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER_VNIR, description='Output VNIR VRT', defaultValue='EnMAP_L1B_VNIR.vrt'
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER_SWIR, description='Output SWIR VRT', defaultValue='EnMAP_L1B_SWIR.vrt'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        dsVnir, dsSwir = importEnmapL1B(
            filenameMetadataXml=self.parameter(parameters, self.P_FILE, context),
            filenameVnir=self.parameter(parameters, self.P_OUTRASTER_VNIR, context),
            filenameSwir=self.parameter(parameters, self.P_OUTRASTER_SWIR, context),
        )
        return {
            self.P_OUTRASTER_VNIR: dsVnir.GetDescription(),
            self.P_OUTRASTER_SWIR: dsSwir.GetDescription(),
        }
