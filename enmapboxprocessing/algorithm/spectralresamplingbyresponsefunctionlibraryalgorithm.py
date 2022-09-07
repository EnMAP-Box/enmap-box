import traceback
from collections import OrderedDict
from typing import Dict, Any, List, Tuple

from enmapbox.qgispluginsupport.qps.speclib import FIELD_VALUES
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibrary
from enmapboxprocessing.algorithm.spectralresamplingbyresponsefunctionconvolutionalgorithmbase import \
    RESPONSE_CUTOFF_VALUE, RESPONSE_CUTOFF_DIGITS
from enmapboxprocessing.algorithm.spectralresamplingtocustomsensoralgorithm import \
    SpectralResamplingToCustomSensorAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException,
                       QgsProcessingParameterField)
from typeguard import typechecked


@typechecked
class SpectralResamplingByResponseFunctionLibraryAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Spectral raster layer'
    P_LIBRARY, _LIBRARY = 'library', 'Spectral response function library'
    P_FIELD, _FIELD = 'field', 'Field with spectral profiles used as features'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputResampledRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Spectral resampling (to response function library)'

    def shortDescription(self) -> str:
        return 'Spectrally resample a spectral raster layer by applying spectral response function convolution, ' \
               'with spectral response function stored inside a spectral library. ' \
               'Each spectral profile defines a destination spectral band.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A spectral raster layer to be resampled.'),
            (self._LIBRARY, 'A spectral response function library defining the destination sensor.'),
            (self._FIELD, 'Field with spectral profiles used as spectral response functions. '
                          'If not selected, the default field is used. '
                          'If that is also not specified, an error is raised.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.SpectralResampling.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterVectorLayer(self.P_LIBRARY, self._LIBRARY)
        self.addParameterField(
            self.P_FIELD, self._FIELD, None, self.P_LIBRARY, QgsProcessingParameterField.Any, False, True, False, True
        )
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsSpectralRasterLayer(parameters, self.P_RASTER, context)
        library = self.parameterAsVectorLayer(parameters, self.P_LIBRARY, context)
        binaryField = self.parameterAsField(parameters, self.P_FIELD, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            try:
                spectralLibrary = SpectralLibrary(library.source())
            except Exception as error:
                traceback.print_exc()
                message = f"failed to open spectral library: {error}"
                feedback.reportError(message, fatalError=True)
                raise QgsProcessingException(message)

            responses = OrderedDict()
            if binaryField is None:
                binaryField = FIELD_VALUES

            for profile in spectralLibrary.profiles(profile_field=binaryField):
                # derive to-nanometers scale factor
                wavelength_units = profile.xUnit()
                if wavelength_units.lower() in ['micrometers', 'um']:
                    scale = 1000.
                elif wavelength_units.lower() in ['nanometers', 'nm']:
                    scale = 1.
                else:
                    raise ValueError(f'unsupported wavelength units: {wavelength_units}')
                # prepare responses
                responses[profile.attribute('name')] = [
                    (int(round(x * scale)), round(y, RESPONSE_CUTOFF_DIGITS))  # scale and round
                    for x, y in zip(profile.xValues(), profile.yValues())
                    if y >= RESPONSE_CUTOFF_VALUE  # filter very small weights for better performance
                ]

            # prepare code snippet
            text = ['from collections import OrderedDict',
                    'responses = OrderedDict()']
            for name in responses:
                text.append(f"responses[{repr(name)}] = {responses[name]}")
            code = '\n'.join(text)

            alg = SpectralResamplingToCustomSensorAlgorithm()
            parameters = {
                alg.P_RASTER: raster,
                alg.P_CODE: code,
                alg.P_OUTPUT_RASTER: filename
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
