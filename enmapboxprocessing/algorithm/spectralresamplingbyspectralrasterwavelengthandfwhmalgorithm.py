from typing import Dict, Any, List, Tuple

from enmapboxprocessing.algorithm.spectralresamplingtocustomsensoralgorithm import \
    SpectralResamplingToCustomSensorAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback)
from typeguard import typechecked


@typechecked
class SpectralResamplingBySpectralRasterWavelengthAndFwhmAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Spectral raster layer'
    P_RESPONSE_RASTER, _RESPONSE_RASTER = 'responseRaster', 'Spectral raster layer with wavelength and FWHM'
    P_SAVE_RESPONSE_FUNCTION, _SAVE_RESPONSE_FUNCTION = 'saveResponseFunction', 'Save spectral response function'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputResampledRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Spectral resampling (to spectral raster layer wavelength and FWHM)'

    def shortDescription(self) -> str:
        return 'Spectrally resample a spectral raster layer by applying spectral response function convolution, ' \
               'with spectral response function derived from wavelength and FWHM information stored inside a ' \
               'spectral raster layer.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A spectral raster layer to be resampled.'),
            (self._RESPONSE_RASTER, 'A spectral raster layer with center wavelength and FWHM information '
                                    'defining the destination sensor.'),
            (self._SAVE_RESPONSE_FUNCTION,
             'Whether to save the spectral response function library as *.srf.gpkg sidecar file.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.SpectralResampling.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterRasterLayer(self.P_RESPONSE_RASTER, self._RESPONSE_RASTER)
        self.addParameterBoolean(self.P_SAVE_RESPONSE_FUNCTION, self._SAVE_RESPONSE_FUNCTION, False, True, True)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsSpectralRasterLayer(parameters, self.P_RASTER, context)
        responseRaster = self.parameterAsSpectralRasterLayer(
            parameters, self.P_RESPONSE_RASTER, context, checkFwhm=True
        )
        saveResponseFunction = self.parameterAsBoolean(parameters, self.P_SAVE_RESPONSE_FUNCTION, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # prepare code snippet
            reader = RasterReader(responseRaster)
            text = ['from collections import OrderedDict',
                    'responses = OrderedDict()']
            for bandNo in range(1, reader.bandCount() + 1):
                text.append(f"responses[{round(reader.wavelength(bandNo), 1)}] = {round(reader.fwhm(bandNo), 1)}")
            code = '\n'.join(text)

            alg = SpectralResamplingToCustomSensorAlgorithm()
            parameters = {
                alg.P_RASTER: raster,
                alg.P_CODE: code,
                alg.P_SAVE_RESPONSE_FUNCTION: saveResponseFunction,
                alg.P_OUTPUT_RASTER: filename
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
