import zipfile
from os.path import basename, splitext
from typing import Dict, Any, List, Tuple
from xml.etree import ElementTree

import numpy as np
from osgeo import gdal
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsRasterLayer, QgsMapLayer

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils


@typechecked
class ImportEnmapL2AAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file or ZIP file'
    P_EXCLUDE_NO_DATA_BANDS, _EXCLUDE_NO_DATA_BANDS, = 'excludeNoDataBands', 'Exclude no data bands'
    P_DETECTOR_OVERLAP, _DETECTOR_OVERLAP = 'detectorOverlap', 'Detector overlap region'
    O_DETECTOR_OVERLAP = [
        'Order by detector (VNIR, SWIR)', 'Order by wavelength (default order)', 'VNIR only', 'SWIR only'
    ]
    (OrderByDetectorOverlapOption, OrderByWavelengthOverlapOption, VnirOnlyOverlapOption,
     SwirOnlyOverlapOption) = range(4)
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputEnmapL2ARaster', 'Output raster layer'

    def displayName(self):
        return 'Import EnMAP L2A product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled into the 0 to 1 range.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The metadata XML file or the ZIP file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the metadata XML file directly from your system file browser '
                         'a) onto the EnMAP-Box map view area, or b) onto the Sensor Product Import panel.'),
            (self._EXCLUDE_NO_DATA_BANDS, 'Whether to exclude no data bands.'),
            (self._DETECTOR_OVERLAP, 'Different options for handling the detector overlap region from 900 to 1000 '
                                     'nanometers. For the Moving average filter, a kernel size of 3 is used.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='XML',
            fileFilter='Metadata or ZIP file (*-METADATA.XML *.ZIP);;All files (*.*)'
        )
        self.addParameterBoolean(self.P_EXCLUDE_NO_DATA_BANDS, self._EXCLUDE_NO_DATA_BANDS, True, True)
        self.addParameterEnum(
            self.P_DETECTOR_OVERLAP, self._DETECTOR_OVERLAP, self.O_DETECTOR_OVERLAP, False, self.SwirOnlyOverlapOption
        )
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, file: str) -> bool:
        isValid = basename(file).startswith('ENMAP')
        if file.lower().endswith('.xml'):
            isValid &= basename(file).endswith('METADATA.XML') or basename(file).endswith('METADATA.xml')
        elif file.lower().endswith('.zip'):
            pass
        else:
            isValid = False
        isValid &= 'L2A' in basename(file)
        return isValid

    def defaultParameters(self, xmlOrZipFilename: str):
        if xmlOrZipFilename.lower().endswith('.zip'):
            raise NotImplementedError()
        filename = xmlOrZipFilename
        filename = filename.replace('METADATA.XML', 'SPECTRAL_IMAGE.vrt')
        filename = filename.replace('METADATA.xml', 'SPECTRAL_IMAGE.vrt')
        return {
            self.P_FILE: xmlOrZipFilename,
            self.P_OUTPUT_RASTER: filename
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        xmlOrZipFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        excludeNoDataBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_NO_DATA_BANDS, context)
        detectorOverlap = self.parameterAsEnum(parameters, self.P_DETECTOR_OVERLAP, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'ENMAP01-____L2A-DT000326721_20170626T102020Z_001_V000204_20200406T201930Z-METADATA.XML'
            if not self.isValidFile(xmlOrZipFilename):
                message = (f'not a valid EnMAP L2A product: {xmlOrZipFilename}\n'
                           f'Hint: relocating the product to a directory with a shorter path may help in some cases.')
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            # read metadata
            isZip = xmlOrZipFilename.lower().endswith('.zip')
            if isZip:
                with zipfile.ZipFile(xmlOrZipFilename) as z:
                    productName = splitext(basename(xmlOrZipFilename))[0]
                    with z.open(productName + '/' + productName + '-METADATA.XML') as f:
                        tree = ElementTree.parse(f)
                        root = tree.getroot()
            else:
                root = ElementTree.parse(xmlOrZipFilename).getroot()
            wavelength = [float(item.text) for item in
                          root.findall('specific/bandCharacterisation/bandID/wavelengthCenterOfBand')]
            fwhm = [item.text for item in root.findall('specific/bandCharacterisation/bandID/FWHMOfBand')]
            gains = [item.text for item in root.findall('specific/bandCharacterisation/bandID/GainOfBand')]
            offsets = [item.text for item in root.findall('specific/bandCharacterisation/bandID/OffsetOfBand')]
            bandStatisticsStdDev = [item.text for item in root.findall('product/bandStatistics/bandID/stdDeviation')]
            bandStatisticsMean = [item.text for item in root.findall('product/bandStatistics/bandID/mean')]

            # make sure that wavelength are sorted
            values = np.array(wavelength, float)
            assert np.all(values[:-1] <= values[1:]), 'wavelength are assumed to be sorted'

            spectralImageFilename = ImportEnmapL1BAlgorithm.findSpectralImageFilename(
                xmlOrZipFilename, '-SPECTRAL_IMAGE'
            )

            # make sure, that EOLab ARD products are not imported as VRT
            if '_COG' in spectralImageFilename:
                feedback.pushWarning(
                    'Detected L2A ARD product. It is recommended to NOT store such products as VRT. '
                    'Visualization and processing will be very slow. Use GeoTiff format (*.tif) instead.'
                )

            # prepare band list
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

            if excludeNoDataBands:  # see issues #267 and #974
                bandList = [bandNo for bandNo in bandList
                            if bandStatisticsStdDev[bandNo - 1] != '0' or bandStatisticsMean[bandNo - 1] != '-1000000']

            # update metadata
            wavelength = [str(wavelength[bandNo - 1]) for bandNo in bandList]
            fwhm = [fwhm[bandNo - 1] for bandNo in bandList]
            gains = [gains[bandNo - 1] for bandNo in bandList]
            offsets = [offsets[bandNo - 1] for bandNo in bandList]

            # build band stack
            alg = TranslateRasterAlgorithm()
            parameters = {
                alg.P_RASTER: spectralImageFilename,
                alg.P_BAND_LIST: bandList,
                alg.P_OUTPUT_RASTER: filename
            }
            alg.runAlg(alg, parameters, None, feedback2)

            ds = gdal.Open(filename)
            writer = RasterWriter(ds)
            for bandNo in writer.bandNumbers():
                writer.setBandName(f'band {bandList[bandNo - 1]} ({wavelength[bandNo - 1]} Nanometers)', bandNo)
                writer.setScale(float(gains[bandNo - 1]), bandNo)
                writer.setOffset(float(offsets[bandNo - 1]), bandNo)
                writer.setFwhm(float(fwhm[bandNo - 1]), bandNo)
                writer.setWavelength(float(wavelength[bandNo - 1]), bandNo)
            writer.close()

            # setup default renderer
            layer = QgsRasterLayer(filename)
            reader = RasterReader(layer)
            redBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['R'][0])
            greenBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['G'][0])
            blueBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['B'][0])
            redMin, redMax = reader.provider.cumulativeCut(
                redBandNo, 0.02, 0.98, reader.extent(), int(QgsRasterLayer.SAMPLE_SIZE)
            )
            greenMin, greenMax = reader.provider.cumulativeCut(
                greenBandNo, 0.02, 0.98, reader.extent(), int(QgsRasterLayer.SAMPLE_SIZE)
            )
            blueMin, blueMax = reader.provider.cumulativeCut(
                blueBandNo, 0.02, 0.98, reader.extent(), int(QgsRasterLayer.SAMPLE_SIZE)
            )
            renderer = Utils().multiBandColorRenderer(
                reader.provider, [redBandNo, greenBandNo, blueBandNo], [redMin, greenMin, blueMin],
                [redMax, greenMax, blueMax]
            )
            layer.setRenderer(renderer)
            layer.saveDefaultStyle(QgsMapLayer.StyleCategory.Rendering)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
