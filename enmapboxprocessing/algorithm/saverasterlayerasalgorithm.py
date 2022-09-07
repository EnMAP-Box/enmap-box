from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class SaveRasterAsAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Raster layer'
    P_COPY_METADATA, _COPY_METADATA = 'copyMetadata', 'Copy metadata'
    P_COPY_STYLE, _COPY_STYLE = 'copyStyle', 'Copy style'
    P_CREATION_PROFILE, _CREATION_PROFILE = 'creationProfile', 'Output options'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputRaster', 'Output raster layer'

    def displayName(self):
        return 'Save raster layer as'

    def shortDescription(self):
        return 'Saves a raster layer as a GeoTiff, ENVI or VRT file. ' \
               'This is a slimmed down version of the more powerful "Translate raster layer" algorithm.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'Source raster layer.'),
            (self._COPY_METADATA, 'Whether to copy metadata from source to destination.'),
            (self._COPY_STYLE, 'Whether to copy style from source to destination.'),
            (self._CREATION_PROFILE, 'Output format and creation options. '
                                     'The default format is GeoTiff with creation options: '
                                     '' + ', '.join(self.DefaultGTiffCreationOptions)),
            (self._CREATION_PROFILE, 'Output format and creation options.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.RasterConversion.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterBoolean(self.P_COPY_METADATA, self._COPY_METADATA, defaultValue=True)
        self.addParameterBoolean(self.P_COPY_STYLE, self._COPY_STYLE, defaultValue=True)
        self.addParameterCreationProfile(self.P_CREATION_PROFILE, self._CREATION_PROFILE, '', True, False)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER, allowEnvi=True, allowVrt=True)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsRasterLayer(parameters, self.P_RASTER, context)
        copyMetadata = self.parameterAsBoolean(parameters, self.P_COPY_METADATA, context)
        copyStyle = self.parameterAsBoolean(parameters, self.P_COPY_STYLE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            alg = TranslateRasterAlgorithm()
            parameters = {
                alg.P_RASTER: raster,
                alg.P_COPY_METADATA: copyMetadata,
                alg.P_COPY_STYLE: copyStyle,
                alg.P_OUTPUT_RASTER: filename
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
