from os.path import splitext
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.qgispluginsupport.qps.speclib.io.envi import readENVIHeader
from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.spectralresamplingtocustomsensoralgorithm import \
    SpectralResamplingToCustomSensorAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.enviutils import EnviUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException


@typechecked
class SpectralResamplingByWavelengthAndFwhmAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Spectral raster layer'
    P_RESPONSE_FILE, _RESPONSE_FILE = 'responseFile', 'File with wavelength and FWHM'
    P_FWHM, _FWHM = 'fwhm', 'FWHM'
    P_OUTPUT_LIBRARY, _OUTPUT_LIBRARY = 'outputResponseFunctionLibrary', 'Output spectral response function library'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputResampledRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Spectral resampling (to wavelength and FWHM)'

    def shortDescription(self) -> str:
        return 'Spectrally resample a spectral raster layer by applying spectral response function convolution, ' \
               'with spectral response function derived from wavelength and FWHM information.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A spectral raster layer to be resampled.'),
            (self._RESPONSE_FILE,
             'A file with center wavelength and FWHM information defining the destination sensor. '
             'Possible inputs are i) raster files, ii) ENVI Spectral Library files, iii) ENVI Header files, '
             'and iv) CSV table files with wavelength and fwhm columns.'),
            (self._FWHM,
             'Specify a FWHM value used for each band. This overwrites FWHM values read from file'),
            (self._OUTPUT_LIBRARY, self.GeoJsonFileDestination),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.SpectralResampling.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterFile(self.P_RESPONSE_FILE, self._RESPONSE_FILE)
        self.addParameterFloat(self.P_FWHM, self._FWHM, None, True, 0, None, True)
        self.addParameterFileDestination(
            self.P_OUTPUT_LIBRARY, self._OUTPUT_LIBRARY, self.GeoJsonFileFilter, None, True, True
        )
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsSpectralRasterLayer(parameters, self.P_RASTER, context)
        responseFile = self.parameterAsFile(parameters, self.P_RESPONSE_FILE, context)
        fwhmValue = self.parameterAsFloat(parameters, self.P_FWHM, context)
        filenameSrf = self.parameterAsFileOutput(parameters, self.P_OUTPUT_LIBRARY, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # prepare code snippet
            if splitext(responseFile)[1].lower() == '.hdr':
                # handle ENVI header case
                metadata = EnviUtils().readEnviHeader(responseFile)
                srcUnits = metadata['wavelength units']
                f = Utils().wavelengthUnitsConversionFactor(srcUnits, 'nanometers')
                wavelengths = [f * float(v) for v in metadata['wavelength']]
                if fwhmValue is None:
                    fwhms = [f * float(v) for v in metadata['fwhm']]
                else:
                    fwhms = [fwhmValue] * len(wavelengths)
            elif splitext(responseFile)[1].lower() == '.csv':
                # handle CSV with wavelength and fwhm case
                array = np.loadtxt(responseFile, delimiter=",", dtype=str)
                if array[0, 0] != 'wavelength':
                    raise QgsProcessingException(
                        f'first column is expected to be named "wavelength", found "{array[0, 0]}"')
                if array[0, 1] != 'fwhm':
                    raise QgsProcessingException(f'second column is expected to be named "fwhm", found "{array[0, 1]}"')
                wavelengths = list(map(float, array[1:, 0].tolist()))
                if fwhmValue is None:
                    fwhms = list(map(float, array[1:, 1].tolist()))
                else:
                    fwhms = [fwhmValue] * len(wavelengths)
            else:
                try:
                    # handle raster case
                    reader = RasterReader(responseFile)
                    wavelengths = [reader.wavelength(bandNo) for bandNo in reader.bandNumbers()]
                    if fwhmValue is None:
                        fwhms = [reader.fwhm(bandNo) for bandNo in reader.bandNumbers()]
                    else:
                        fwhms = [fwhmValue] * len(wavelengths)
                except RuntimeError as error:
                    # handle ENVI Speclib case
                    if "GDAL does not support 'ENVI Spectral Library' type files." in str(error):
                        metadata = readENVIHeader(responseFile, True)
                        srcUnits = metadata['wavelength units']
                        f = Utils().wavelengthUnitsConversionFactor(srcUnits, 'nanometers')
                        wavelengths = [f * w for w in metadata['wavelength']]
                        if fwhmValue is None:
                            fwhms = [f * w for w in metadata['fwhm']]
                        else:
                            fwhms = [fwhmValue] * len(wavelengths)
                    else:
                        raise ValueError(f'{responseFile} not supported')

            text = ['from collections import OrderedDict',
                    'responses = OrderedDict()']
            for wavelength, fwhm in zip(wavelengths, fwhms):
                text.append(f"responses[{round(wavelength, 1)}] = {round(fwhm, 1)}")

            code = '\n'.join(text)

            alg = SpectralResamplingToCustomSensorAlgorithm()
            parameters = {
                alg.P_RASTER: raster,
                alg.P_CODE: code,
                alg.P_OUTPUT_LIBRARY: filenameSrf,
                alg.P_OUTPUT_RASTER: filename
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            result = {
                self.P_OUTPUT_LIBRARY: filenameSrf,
                self.P_OUTPUT_RASTER: filename
            }
            self.toc(feedback, result)

        return result
