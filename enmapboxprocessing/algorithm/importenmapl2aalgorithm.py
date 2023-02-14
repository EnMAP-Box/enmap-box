from os.path import basename
from typing import Dict, Any, List, Tuple
from xml.etree import ElementTree

import numpy as np
from osgeo import gdal

from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.algorithm.vrtbandmathalgorithm import VrtBandMathAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.gdalutils import GdalUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from enmapbox.typeguard import typechecked


@typechecked
class ImportEnmapL2AAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_DETECTOR_OVERLAP, _DETECTOR_OVERLAP = 'detectorOverlap', 'Detector overlap region'
    O_DETECTOR_OVERLAP = ['Order by wavelength', 'Moving average filter', 'VNIR only', 'SWIR only']
    OrderByWavelengthOverlapOption, MovingAverageFilterOverlapOption, VnirOnlyOverlapOption, SwirOnlyOverlapOption = \
        range(4)
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputEnmapL2ARaster', 'Output raster layer'

    def displayName(self):
        return 'Import EnMAP L2A product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled into the 0 to 1 range.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The metadata XML file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the metadata XML file directly from your system file browser onto '
                         'the EnMAP-Box map view area.'),
            (self.P_DETECTOR_OVERLAP, 'Different options for handling the detector overlap region from 900 to 1000 '
                                      'nanometers. For the Moving average filter, a kernel size of 3 is used.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FILE, self._FILE, extension='xml',
                              fileFilter='Metadata file (*-METADATA.xml);;All files (*.*)')
        self.addParameterEnum(
            self.P_DETECTOR_OVERLAP, self._DETECTOR_OVERLAP, self.O_DETECTOR_OVERLAP, False, self.SwirOnlyOverlapOption
        )
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('ENMAP') & \
               basename(file).endswith('METADATA.XML') & \
               ('L2A' in basename(file))

    def defaultParameters(self, xmlFilename: str):
        return {
            self.P_FILE: xmlFilename,
            self.P_OUTPUT_RASTER: xmlFilename.replace('METADATA.XML', 'SPECTRAL_IMAGE.vrt'),
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        xmlFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        detectorOverlap = self.parameterAsEnum(parameters, self.P_DETECTOR_OVERLAP, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)
        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'ENMAP01-____L2A-DT000326721_20170626T102020Z_001_V000204_20200406T201930Z-METADATA.XML'
            if not self.isValidFile(xmlFilename):
                message = f'not a valid EnMAP L2A product: {xmlFilename}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            # read metadata
            root = ElementTree.parse(xmlFilename).getroot()
            wavelength = [item.text for item in
                          root.findall('specific/bandCharacterisation/bandID/wavelengthCenterOfBand')]
            fwhm = [item.text for item in root.findall('specific/bandCharacterisation/bandID/FWHMOfBand')]
            gains = [item.text for item in root.findall('specific/bandCharacterisation/bandID/GainOfBand')]
            offsets = [item.text for item in root.findall('specific/bandCharacterisation/bandID/OffsetOfBand')]

            # make sure that wavelength are sorted
            values = np.array(wavelength, float)
            assert np.all(values[:-1] <= values[1:]), 'wavelength are assumed to be sorted'

            # create VRT
            if detectorOverlap != self.MovingAverageFilterOverlapOption:
                vnirWavelength = [float(item.text)
                                  for item in root.findall('product/smileCorrection/VNIR/bandID/wavelength')
                                  if 900 <= float(item.text) <= 1000]
                swirWavelength = [float(item.text)
                                  for item in root.findall('product/smileCorrection/SWIR/bandID/wavelength')
                                  if 900 <= float(item.text) <= 1000]

                if detectorOverlap == self.OrderByWavelengthOverlapOption:
                    bandList = list(range(1, len(wavelength) + 1))
                elif detectorOverlap == self.VnirOnlyOverlapOption:
                    bandList = list()
                    for bandNo, w in enumerate(wavelength, 1):
                        w = float(w)
                        if 900 <= w <= 1000:
                            if np.min(np.abs(np.subtract(swirWavelength, w))) < 0.01:
                                continue  # skip SWIR bands
                        bandList.append(bandNo)
                elif detectorOverlap == self.SwirOnlyOverlapOption:
                    bandList = list()
                    for bandNo, w in enumerate(wavelength, 1):
                        w = float(w)
                        if 900 <= w <= 1000:
                            if np.min(np.abs(np.subtract(vnirWavelength, w))) < 0.01:
                                continue  # skip VNIR bands
                        bandList.append(bandNo)
                else:
                    raise ValueError()

                ds = gdal.Open(ImportEnmapL1BAlgorithm.findFilename(
                    xmlFilename.replace('-METADATA.XML', '-SPECTRAL_IMAGE'))
                )
                options = gdal.TranslateOptions(format='VRT', outputType=gdal.GDT_Float32, bandList=bandList)
                ds: gdal.Dataset = gdal.Translate(destName=filename, srcDS=ds, options=options)
            else:
                # create VRT stack with all bands
                spectralImageFilename = ImportEnmapL1BAlgorithm.findFilename(
                    xmlFilename.replace('-METADATA.XML', '-SPECTRAL_IMAGE')
                )
                reader = RasterReader(spectralImageFilename)
                ds = gdal.Open(spectralImageFilename)
                noDataValue = ds.GetRasterBand(1).GetNoDataValue()
                options = gdal.TranslateOptions(format='VRT', outputType=gdal.GDT_Float32)
                vrtStackFilename = Utils.tmpFilename(filename, 'raster.vrt')
                gdal.Translate(destName=vrtStackFilename, srcDS=ds, options=options)

                # create VRT bands in the overlap region
                vrtBandFilenames = list()
                bandNumbers = list()
                for bandNo, w in enumerate(wavelength, 1):
                    w = float(w)
                    if 900 <= w <= 1000:
                        code = 'import numpy as np\n\n' \
                               f'noDataValue = {noDataValue}\n\n' \
                               'def ufunc(in_ar, out_ar, *args, **kwargs):\n' \
                               '    invalid = np.any(in_ar == noDataValue, axis=0)\n' \
                               '    out_ar[:] = np.mean(in_ar, axis=0)\n' \
                               '    out_ar[invalid] = noDataValue'
                        alg = VrtBandMathAlgorithm()
                        vrtBandFilename = Utils.tmpFilename(filename, f'band{bandNo}.vrt')
                        parameters = {
                            alg.P_RASTER: spectralImageFilename,
                            alg.P_BAND_LIST: [bandNo - 1, bandNo, bandNo + 1],
                            alg.P_BAND_NAME: reader.bandName(bandNo),
                            alg.P_NODATA: noDataValue,
                            alg.P_DATA_TYPE: alg.Float32,
                            alg.P_CODE: code,
                            alg.P_OUTPUT_VRT: vrtBandFilename
                        }
                        self.runAlg(alg, parameters, None, feedback2, context, True)

                        vrtBandFilenames.append(vrtBandFilename)
                        bandNumbers.append(1)
                    else:
                        vrtBandFilenames.append(vrtStackFilename)
                        bandNumbers.append(bandNo)

                GdalUtils.stackVrtBands(filename, vrtBandFilenames, bandNumbers)
                ds: gdal.Dataset = gdal.Open(filename)
                bandList = list(range(1, len(wavelength) + 1))

            # update metadata
            wavelength = [wavelength[bandNo - 1] for bandNo in bandList]
            fwhm = [fwhm[bandNo - 1] for bandNo in bandList]
            gains = [gains[bandNo - 1] for bandNo in bandList]
            offsets = [offsets[bandNo - 1] for bandNo in bandList]

            for values in [wavelength, fwhm, gains, offsets]:
                assert len(values) == ds.RasterCount

            ds.SetMetadataItem('wavelength', '{' + ', '.join(wavelength) + '}', 'ENVI')
            ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            ds.SetMetadataItem('fwhm', '{' + ', '.join(fwhm) + '}', 'ENVI')

            rasterBands = [ds.GetRasterBand(i + 1) for i in range(ds.RasterCount)]
            rasterBand: gdal.Band
            for i, rasterBand in enumerate(rasterBands):
                rasterBand.SetDescription(f'band {i + 1} ({wavelength[i]} Nanometers)')
                rasterBand.SetScale(float(gains[i]))
                rasterBand.SetOffset(float(offsets[i]))
                rasterBand.FlushCache()

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
