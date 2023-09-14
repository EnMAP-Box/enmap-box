from typing import List, Tuple, Dict, Any

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.spectralresamplingbyresponsefunctionlibraryalgorithm import \
    SpectralResamplingByResponseFunctionLibraryAlgorithm
from enmapboxprocessing.algorithm.spectralresamplingbywavelengthandfwhmalgorithm import \
    SpectralResamplingByWavelengthAndFwhmAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import QgsProcessingContext, QgsProcessingFeedback


@typechecked
class SpectralResamplingToSensorAlgorithmBase(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Spectral raster layer'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputResampledRaster', 'Output raster layer'

    sensor = None

    def displayName(self) -> str:
        return f'Spectral resampling (to {self.sensor.shortname})'

    def shortDescription(self) -> str:
        link = self.htmlLink(self.sensor.website, 'mission website')
        return f'Spectral resampling to {self.sensor.shortname} sensor.\n' \
               f'For more information see the {link}.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A spectral raster layer to be resampled.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.SpectralResampling.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsSpectralRasterLayer(parameters, self.P_RASTER, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if self.sensor.responseFunctionFile.endswith('.csv'):
                alg = SpectralResamplingByWavelengthAndFwhmAlgorithm()
                parameters = {
                    alg.P_RASTER: raster,
                    alg.P_RESPONSE_FILE: self.sensor.responseFunctionFile,
                    alg.P_OUTPUT_RASTER: filename
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
            elif self.sensor.responseFunctionFile.endswith('.geojson'):
                alg = SpectralResamplingByResponseFunctionLibraryAlgorithm()
                parameters = {
                    alg.P_RASTER: raster,
                    alg.P_LIBRARY: self.sensor.responseFunctionFile,
                    alg.P_FIELD: 'response',
                    alg.P_OUTPUT_RASTER: filename
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
            else:
                raise ValueError()

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
