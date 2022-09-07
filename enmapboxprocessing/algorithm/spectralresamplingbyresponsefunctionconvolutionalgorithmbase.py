import inspect
from collections import OrderedDict
from math import ceil, sqrt, pi, exp
from typing import Dict, Any, List, Tuple, Union
from warnings import warn

import numpy as np
from osgeo import gdal

from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibrary
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import SpectralProfile
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.typing import Array3d, Number
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from typeguard import typechecked

RESPONSE_CUTOFF_VALUE = 0.001
RESPONSE_CUTOFF_DIGITS = 3


@typechecked
class SpectralResamplingByResponseFunctionConvolutionAlgorithmBase(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Spectral raster layer'
    P_CODE, _CODE = 'response', 'Spectral response function'
    P_SAVE_RESPONSE_FUNCTION, _SAVE_RESPONSE_FUNCTION = 'saveResponseFunction', 'Save spectral response function'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputResampledRaster', 'Output raster layer'
    A_CODE = False

    def displayName(self) -> str:
        raise NotImplementedError

    def shortDescription(self) -> str:
        return 'Spectrally resample a spectral raster layer by applying spectral response function convolution.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A spectral raster layer to be resampled.'),
            (self._CODE, 'Python code specifying the spectral response function.'),
            (self._SAVE_RESPONSE_FUNCTION,
             'Whether to save the spectral response function library as *.srf.gpkg sidecar file.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.SpectralResampling.value

    def code(self):
        raise NotImplementedError()

    def defaultCodeAsString(self):
        try:
            lines = [line[8:] for line in inspect.getsource(self.code).split('\n')][1:-2]
        except OSError:
            lines = ['']
        lines = '\n'.join(lines)
        return lines

    def parameterAsResponses(
            self, parameters: Dict[str, Any], name, context: QgsProcessingContext
    ) -> Dict[Union[str, float], Union[List[Tuple[int, float]], Number]]:
        namespace = dict()
        code = self.parameterAsString(parameters, name, context)
        exec(code, namespace)
        responses = namespace['responses']
        return responses

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterCode(self.P_CODE, self._CODE, self.defaultCodeAsString(), advanced=self.A_CODE)
        self.addParameterBoolean(self.P_SAVE_RESPONSE_FUNCTION, self._SAVE_RESPONSE_FUNCTION, False, True, True)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsSpectralRasterLayer(parameters, self.P_RASTER, context)
        responses = self.parameterAsResponses(parameters, self.P_CODE, context)
        saveResponseFunction = self.parameterAsBoolean(parameters, self.P_SAVE_RESPONSE_FUNCTION, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        maximumMemoryUsage = gdal.GetCacheMax()

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # convert FWHM specifications to fully defined response function
            responses2 = OrderedDict()
            for i, (k, v) in enumerate(responses.items()):
                if isinstance(k, (int, float)):
                    fwhm = float(v)
                    sigma = fwhm / 2.355
                    x0 = float(k)
                    xs = list()
                    weights = list()
                    a = 2 * sigma ** 2
                    b = sigma * sqrt(2 * pi)
                    for x in range(int(x0 - sigma * 3), int(x0 + sigma * 3) + 2):
                        c = -(x - x0) ** 2
                        fx = exp(c / a) / b
                        weights.append(fx)
                        xs.append(x)
                    weights = np.divide(weights, np.max(weights))  # scale to 0-1 range
                    #                responses2[f'Band {i + 1} ({k} Nanometers)'] = [(x, round(w, RESPONSE_CUTOFF_DIGITS)) for x, w in
                    #                                                                zip(xs, weights)]
                    responses2[f'band {i + 1}'] = [(x, round(w, RESPONSE_CUTOFF_DIGITS)) for x, w in
                                                   zip(xs, weights)]

                else:
                    responses2[k] = v
            responses = responses2

            feedback.getQgsFeedback().pushInfo('Spectral response functions:')  # never silence this info!
            for name in responses:
                feedback.getQgsFeedback().pushInfo(f"responses['{name}'] = {responses[name]}")

            # check if wavelength have single nanometer step
            for name in responses:
                values = np.array([v for v, _ in responses[name]])
                differences = np.subtract(values[1:], values[:-1])
                if not np.all(differences == 1):
                    message = f'invalid response function wavelength resolution for "{name}" band\n' \
                              f'wavelength: {values}\n' \
                              f'difference: {differences}\n' \
                              f'check wavelength region around: {values[:-1][differences != 1]}'
                    feedback.reportError(message, True)
                    raise QgsProcessingException(message)

            reader = RasterReader(raster)
            wavelength = [reader.wavelength(i + 1) for i in range(reader.bandCount())]
            outputBandCount = len(responses)
            outputNoDataValue = reader.noDataValue()

            writer = Driver(filename, feedback=feedback).createLike(reader, reader.dataType(), outputBandCount)
            lineMemoryUsage = reader.lineMemoryUsage() * 2
            blockSizeY = min(raster.height(), ceil(maximumMemoryUsage / lineMemoryUsage))
            blockSizeX = raster.width()
            for block in reader.walkGrid(blockSizeX, blockSizeY, feedback):
                array = reader.arrayFromBlock(block)
                outarray = self.resampleData(array, wavelength, responses, outputNoDataValue, feedback)
                if outputNoDataValue is not None:
                    marray = np.all(reader.maskArray(array), axis=0)
                    for arr in outarray:
                        arr[np.logical_not(marray)] = outputNoDataValue
                writer.writeArray(outarray, block.xOffset, block.yOffset)

            outputWavelength = list()
            for name in responses:
                values = responses[name]
                outputWavelength.append(
                    np.average(
                        [tup[0] for tup in values],
                        weights=[tup[1] for tup in values]
                    )
                )

            for bandNo, bandName in enumerate(responses, 1):
                wl = round(outputWavelength[bandNo - 1], 1)
                writer.setWavelength(wl, bandNo)
                writer.setBandName(bandName + f' ({wl} Nanometers)', bandNo)
            writer.setNoDataValue(outputNoDataValue, bandNo)
            writer.close()

            if saveResponseFunction:

                library = SpectralLibrary()
                profiles = list()
                for name in responses:
                    values = responses[name]
                    profile = SpectralProfile()
                    profile.setName(name)
                    x = [xi for xi, yi in values]
                    y = [yi for xi, yi in values]
                    profile.setValues(x, y, 'Nanometers')
                    profiles.append(profile)
                library.startEditing()
                library.addProfiles(profiles)
                library.commitChanges()
                library.write(filename + '.srf.gpkg')

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result

    @staticmethod
    def resampleData(
            array: Array3d, wavelength: List, responses: Dict[str, List[Tuple[int, float]]], noDataValue: float,
            feedback: QgsProcessingFeedback
    ) -> Array3d:
        wavelength = [int(round(v)) for v in wavelength]
        outarray = list()
        for name in responses:
            weightsByWavelength = dict(responses[name])
            indices = list()
            weights = list()
            for index, wl in enumerate(wavelength):
                weight = weightsByWavelength.get(wl)
                if weight is not None:
                    indices.append(index)
                    weights.append(weight)
            if len(indices) == 0:
                message = f'no source bands ({min(wavelength)} to {max(wavelength)} nanometers) ' \
                          f'are covert by target band "{name}" ' \
                          f'({min(weightsByWavelength.keys())} to {max(weightsByWavelength.keys())} nanometers), ' \
                          f'which will result in output band filled with no data values'
                warn(message)
                feedback.pushWarning(message)
                outarray.append(np.full_like(array[0], noDataValue, dtype=array[0].dtype))
            else:
                weights = np.divide(weights, np.sum(weights))
                outarray.append(np.average([array[i] for i in indices], 0, weights))

        return outarray
