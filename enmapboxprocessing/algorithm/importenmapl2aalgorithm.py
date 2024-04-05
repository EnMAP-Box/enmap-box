from os.path import basename
from typing import Dict, Any, List, Tuple
from xml.etree import ElementTree

import numpy as np
from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.algorithm.subsetrasterbandsalgorithm import SubsetRasterBandsAlgorithm
from enmapboxprocessing.algorithm.vrtbandmathalgorithm import VrtBandMathAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.gdalutils import GdalUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsRasterLayer, QgsMapLayer


@typechecked
class ImportEnmapL2AAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_SET_BAD_BANDS, _SET_BAD_BANDS = 'setBadBands', 'Set bad bands'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS, = 'excludeBadBands', 'Exclude bad bands'
    P_DETECTOR_OVERLAP, _DETECTOR_OVERLAP = 'detectorOverlap', 'Detector overlap region'
    O_DETECTOR_OVERLAP = [
        'Order by detector (VNIR, SWIR)', 'Order by wavelength (default order)', 'Moving average filter', 'VNIR only',
        'SWIR only'
    ]
    OrderByDetectorOverlapOption, OrderByWavelengthOverlapOption, MovingAverageFilterOverlapOption, \
    VnirOnlyOverlapOption, SwirOnlyOverlapOption = range(5)
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
                         'you may drag&drop the metadata XML file directly from your system file browser '
                         'a) onto the EnMAP-Box map view area, or b) onto the Sensor Product Import panel.'),
            (self._SET_BAD_BANDS, 'Whether to mark no data bands as bad bands.'),
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bands.'),
            (self._DETECTOR_OVERLAP, 'Different options for handling the detector overlap region from 900 to 1000 '
                                     'nanometers. For the Moving average filter, a kernel size of 3 is used.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='XML', fileFilter='Metadata file (*-METADATA.XML);;All files (*.*)'
        )
        self.addParameterBoolean(self.P_SET_BAD_BANDS, self._SET_BAD_BANDS, True, True)
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, True, True)
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
        setBadBands = self.parameterAsBoolean(parameters, self.P_SET_BAD_BANDS, context)
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
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
            wavelength = [float(item.text) for item in
                          root.findall('specific/bandCharacterisation/bandID/wavelengthCenterOfBand')]
            fwhm = [item.text for item in root.findall('specific/bandCharacterisation/bandID/FWHMOfBand')]
            gains = [item.text for item in root.findall('specific/bandCharacterisation/bandID/GainOfBand')]
            offsets = [item.text for item in root.findall('specific/bandCharacterisation/bandID/OffsetOfBand')]

            # make sure that wavelength are sorted
            values = np.array(wavelength, float)
            assert np.all(values[:-1] <= values[1:]), 'wavelength are assumed to be sorted'

            vrtTempFilename = Utils.tmpFilename(filename, 'stack.vrt')

            # create VRT
            if detectorOverlap != self.MovingAverageFilterOverlapOption:

                # vnirWavelength = [float(item.text)
                #                  for item in root.findall('product/smileCorrection/VNIR/bandID/wavelength')]
                # swirWavelength = [float(item.text)
                #                  for item in root.findall('product/smileCorrection/SWIR/bandID/wavelength')]

                vnirBandNumbers = [
                    int(text) for text in root.find('specific/vnirProductQuality/expectedChannelsList').text.split(',')
                ]
                swirBandNumbers = [
                    int(text) for text in root.find('specific/swirProductQuality/expectedChannelsList').text.split(',')
                ]

                overlapStart = wavelength[swirBandNumbers[0]]
                overlapEnd = wavelength[vnirBandNumbers[-1]]
                if detectorOverlap == self.OrderByDetectorOverlapOption:
                    bandList = vnirBandNumbers + swirBandNumbers
                elif detectorOverlap == self.OrderByWavelengthOverlapOption:
                    bandList = list(range(1, len(wavelength) + 1))
                elif detectorOverlap == self.VnirOnlyOverlapOption:
                    bandList = vnirBandNumbers
                    bandList.extend([bandNo for bandNo in swirBandNumbers if wavelength[bandNo - 1] > overlapEnd])
                elif detectorOverlap == self.SwirOnlyOverlapOption:
                    bandList = [bandNo for bandNo in vnirBandNumbers if wavelength[bandNo - 1] < overlapStart]
                    bandList.extend(swirBandNumbers)
                else:
                    raise ValueError()

                ds = gdal.Open(ImportEnmapL1BAlgorithm.findFilename(
                    xmlFilename.replace('-METADATA.XML', '-SPECTRAL_IMAGE'))
                )
                options = gdal.TranslateOptions(format='VRT', outputType=gdal.GDT_Float32, bandList=bandList)
                ds: gdal.Dataset = gdal.Translate(destName=vrtTempFilename, srcDS=ds, options=options)
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

                GdalUtils.stackVrtBands(vrtTempFilename, vrtBandFilenames, bandNumbers)
                bandList = list(range(1, len(wavelength) + 1))

            # update metadata
            wavelength = [str(wavelength[bandNo - 1]) for bandNo in bandList]
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

            if setBadBands:  # see issue #267
                reader = RasterReader(ds)
                writer = RasterWriter(ds)
                for bandNo in reader.bandNumbers():
                    feedback.setProgress(bandNo / reader.bandCount() * 100)
                    allNoData = np.all(
                        reader.array(
                            yOffset=int(reader.height() / 2), height=1,  # just check single image line
                            bandList=[bandNo]
                        )[0] == reader.noDataValue(bandNo))
                    if allNoData:
                        writer.setBadBandMultiplier(0, bandNo)
                writer.close()
                del reader, writer
            del ds

            if excludeBadBands:  # see issue #461
                if not setBadBands:
                    raise QgsProcessingException('To "Exclude bad bands", also active "Set bad bands" option.')

            alg = SubsetRasterBandsAlgorithm()
            parameters = {
                alg.P_RASTER: vrtTempFilename,
                alg.P_EXCLUDE_BAD_BANDS: excludeBadBands,
                alg.P_OUTPUT_RASTER: filename
            }
            alg.runAlg(alg, parameters, None, feedback2)

            # setup default renderer
            layer = QgsRasterLayer(filename)
            reader = RasterReader(layer)
            redBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['R'][0])
            greenBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['G'][0])
            blueBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['B'][0])
            redMin, redMax = reader.provider.cumulativeCut(redBandNo, 0.02, 0.98)
            greenMin, greenMax = reader.provider.cumulativeCut(greenBandNo, 0.02, 0.98)
            blueMin, blueMax = reader.provider.cumulativeCut(blueBandNo, 0.02, 0.98)
            renderer = Utils().multiBandColorRenderer(
                reader.provider, [redBandNo, greenBandNo, blueBandNo], [redMin, greenMin, blueMin],
                [redMax, greenMax, blueMax]
            )
            layer.setRenderer(renderer)
            layer.saveDefaultStyle(QgsMapLayer.StyleCategory.Rendering)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
