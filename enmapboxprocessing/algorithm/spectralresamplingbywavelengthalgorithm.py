from os.path import splitext
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.qgispluginsupport.qps.speclib.io.envi import readENVIHeader
from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.enviutils import EnviUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException


@typechecked
class SpectralResamplingByWavelengthAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTER, _RASTER = 'raster', 'Spectral raster layer'
    P_WAVELENGTH_FILE, _WAVELENGTH_FILE = 'wavelengthFile', 'File with wavelength'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputResampledRaster', 'Output raster layer'

    def displayName(self) -> str:
        return 'Spectral resampling (to wavelength)'

    def shortDescription(self) -> str:
        link = EnMAPProcessingAlgorithm.htmlLink(
            'https://en.wikipedia.org/wiki/Linear_interpolation', 'Linear Interpolation Wikipedia Article'
        )
        return 'Spectrally resample a spectral raster layer by applying linear interpolation at given wavelengths.\n' \
               f'See {link} for more details.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTER, 'A spectral raster layer to be resampled.'),
            (self._WAVELENGTH_FILE,
             'A file with center wavelength information defining the destination sensor. '
             'Possible inputs are i) raster files, ii) ENVI Spectral Library files, iii) ENVI Header files, '
             'and iv) CSV table files with wavelength column.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.SpectralResampling.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterRasterLayer(self.P_RASTER, self._RASTER)
        self.addParameterFile(self.P_WAVELENGTH_FILE, self._WAVELENGTH_FILE)
        self.addParameterRasterDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        raster = self.parameterAsSpectralRasterLayer(parameters, self.P_RASTER, context)
        wavelengthFile = self.parameterAsFile(parameters, self.P_WAVELENGTH_FILE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # prepare code snippet
            if splitext(wavelengthFile)[1].lower() == '.hdr':
                # handle ENVI header case
                metadata = EnviUtils().readEnviHeader(wavelengthFile)
                srcUnits = metadata['wavelength units']
                f = Utils().wavelengthUnitsConversionFactor(srcUnits, 'nanometers')
                targetWavelengths = [f * float(v) for v in metadata['wavelength']]
            elif splitext(wavelengthFile)[1].lower() == '.csv':
                # handle CSV with wavelength case
                array = np.loadtxt(wavelengthFile, delimiter=",", dtype=str)
                if array[0, 0] != 'wavelength':
                    raise QgsProcessingException(
                        f'first column is expected to be named "wavelength", found "{array[0, 0]}"')
                targetWavelengths = list(map(float, array[1:, 0].tolist()))
            else:
                try:
                    # handle raster case
                    reader = RasterReader(wavelengthFile)
                    targetWavelengths = [reader.wavelength(bandNo) for bandNo in reader.bandNumbers()]
                except RuntimeError as error:
                    # handle ENVI Speclib case
                    if "GDAL does not support 'ENVI Spectral Library' type files." in str(error):
                        metadata = readENVIHeader(wavelengthFile, True)
                        srcUnits = metadata['wavelength units']
                        f = Utils().wavelengthUnitsConversionFactor(srcUnits, 'nanometers')
                        targetWavelengths = [f * w for w in metadata['wavelength']]
                    else:
                        raise ValueError(f'{wavelengthFile} not supported')

            reader = RasterReader(raster)
            sourceWavelengths = np.array([reader.wavelength(i + 1) for i in range(reader.bandCount())])
            minSourceWavelengths = sourceWavelengths.min()
            maxSourceWavelengths = sourceWavelengths.max()
            outputBandCount = len(targetWavelengths)
            outputNoDataValue = reader.noDataValue()
            if outputNoDataValue is None:
                outputNoDataValue = 0

            writer = Driver(filename, feedback=feedback).createLike(reader, reader.dataType(), outputBandCount)
            for targetBandNo, targetWavelength in enumerate(targetWavelengths, 1):
                feedback.setProgress(targetBandNo / outputBandCount * 100)
                closestBandNo = int(np.argmin(abs(sourceWavelengths - targetWavelength)) + 1)
                if sourceWavelengths[closestBandNo - 1] < targetWavelength:
                    bandNo1, bandNo2 = closestBandNo, closestBandNo + 1
                else:
                    bandNo1, bandNo2 = closestBandNo - 1, closestBandNo
                # fix edge cases
                if bandNo1 < 1:
                    bandNo1, bandNo2 = 1, 2
                if bandNo2 > reader.bandCount():
                    bandNo1, bandNo2 = reader.bandCount() - 1, reader.bandCount()

                weight1 = abs(sourceWavelengths[bandNo2 - 1] - targetWavelength)
                weight2 = abs(sourceWavelengths[bandNo1 - 1] - targetWavelength)
                sumOfWeights = weight1 + weight2
                weight1 /= sumOfWeights
                weight2 /= sumOfWeights
                array1, array2 = reader.array(bandList=[bandNo1, bandNo2])
                marray1, marray2 = reader.maskArray([array1, array2], [bandNo1, bandNo2])
                marray = np.logical_and(marray1, marray2)
                outarray = weight1 * array1 + weight2 * array2
                outarray[~marray] = outputNoDataValue
                if targetWavelength < minSourceWavelengths or targetWavelength > maxSourceWavelengths:
                    outarray[:] = outputNoDataValue
                    writer.setBadBandMultiplier(0, targetBandNo)  # mask as bad band
                writer.writeArray2d(outarray, targetBandNo)

            #for bandNo, targetWavelength in enumerate(targetWavelengths, 1):
                writer.setWavelength(targetWavelength, targetBandNo)
                writer.setNoDataValue(outputNoDataValue, targetBandNo)

            result = {
                self.P_OUTPUT_RASTER: filename
            }
            self.toc(feedback, result)

        return result
