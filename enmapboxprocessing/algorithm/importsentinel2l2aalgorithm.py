import xml.etree.ElementTree as ET
from os.path import basename, dirname, join
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.gdalutils import GdalUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsRasterLayer, QgsMapLayer


@typechecked
class ImportSentinel2L2AAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file or ZIP file'
    P_BAND_LIST, _BAND_LIST = 'bandList', 'Band list'
    O_BAND_LIST = [
        'B1, Coastal aerosol (443 Nanometers)[60 Meter]',
        'B2, Blue (492 Nanometers)[10 Meter]',
        'B3, Green (560 Nanometers)[10 Meter]',
        'B4, Red (665 Nanometers)[10 Meter]',
        'B5, Vegetation red edge (704 Nanometers)[20 Meter]',
        'B6, Vegetation red edge (741 Nanometers)[20 Meter]',
        'B7, Vegetation red edge (783 Nanometers)[20 Meter]',
        'B8, NIR (833 Nanometers)[10 Meter]',
        'B8A, Narrow NIR (865 Nanometers)[20 Meter]',
        'B9, Water vapour (945 Nanometers)[60 Meter]',
        'B11, SWIR (1614 Nanometers)[20 Meter]',
        'B12, SWIR (2202 Nanometers)[20 Meter]'
    ]
    D_BAND_LIST = list(range(len(O_BAND_LIST)))
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputSentinel2L2ARaster', 'Output raster layer'

    def displayName(self):
        return 'Import Sentinel-2 L2A product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength information is set and data is scaled into the 0 to 1 range.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The MTD_MSIL2A.xml metadata file or the ZIP file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the metadata file directly from your system file browser '
                         'a) onto the EnMAP-Box map view area, or b) onto the Sensor Product Import panel.'),
            (self._BAND_LIST, 'Bands to be stacked together. '
                              'Defaults to all bands ordered by center wavelength. '
                              'Note that the destination pixel size matches the smallest/finest '
                              'pixel size over all selected bands (i.e. 10, 20 or 60 meters).'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='xml',
            fileFilter='Metadata or ZIP file file (MTD_MSIL2A.xml *.zip);;All files (*.*)'
        )
        self.addParameterEnum(self.P_BAND_LIST, self._BAND_LIST, self.O_BAND_LIST, True, self.D_BAND_LIST, True)
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, file: str) -> bool:
        if file.endswith('SAFE.zip'):
            isValid = basename(file).startswith('S2')
            isValid &= 'MSIL2A' in basename(file)
        else:
            isValid = basename(file) == 'MTD_MSIL2A.xml'
        return isValid

    def defaultParameters(self, xmlFilename: str):
        dir = dirname(xmlFilename)
        return {
            self.P_FILE: xmlFilename,
            self.P_OUTPUT_RASTER: join(dir, basename(dir)) + '_SR.tif',
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        xmlOrZipFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        bandListIndices = self.parameterAsInts(parameters, self.P_BAND_LIST, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'MTD_MSIL2A.xml'
            if not self.isValidFile(xmlOrZipFilename):
                message = f'not a valid Sentinel-2 L2A product: {xmlOrZipFilename}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            # open subdatasets
            ds = gdal.Open(xmlOrZipFilename)
            if not isinstance(ds, gdal.Dataset):
                message = f'unable to open {xmlOrZipFilename}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)
            xml = ds.GetMetadata_Dict('xml:SENTINEL2')
            if len(xml) == 0:
                message = f'not a valid Sentinel-2 L2A product: {xmlOrZipFilename}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            xml_string = '<?xml version=' + xml['<?xml version']
            xml = ET.fromstring(xml_string)
            xml.find('.//PROCESSING_BASELINE').text

            BAND_INFOS = {}
            BOA_ADD_OFFSETS = {e.attrib['band_id']: float(e.text) for e in xml.findall('.//BOA_ADD_OFFSET')}
            BOA_QUANTIFICATION_VALUE = float(xml.find('.//BOA_QUANTIFICATION_VALUE').text)
            for e in xml.findall('.//Spectral_Information'):
                bid = e.attrib['bandId']
                physicalBand = e.attrib['physicalBand']
                info = {'bandId': bid,
                        'physicalBand': physicalBand,
                        'wl_min': float(e.find('Wavelength/MIN').text),
                        'wl_max': float(e.find('Wavelength/MAX').text),
                        'wl_center': float(e.find('Wavelength/CENTRAL').text),
                        'scale': BOA_QUANTIFICATION_VALUE,
                        'offset': BOA_ADD_OFFSETS.get(bid, 0)
                        }
                BAND_INFOS[physicalBand] = info
                BAND_INFOS[bid] = info

            f10 = ds.GetSubDatasets()[0][0]
            f20 = ds.GetSubDatasets()[1][0]
            f60 = ds.GetSubDatasets()[2][0]
            ds10 = gdal.Open(f10)
            ds20 = gdal.Open(f20)
            ds60 = gdal.Open(f60)

            info = dict()
            info2 = dict()
            for ds, f, res in [(ds10, f10, 10), (ds20, f20, 20), (ds60, f60, 60)]:
                for i in range(ds.RasterCount):
                    bandNo = i + 1
                    rb: gdal.Band = ds.GetRasterBand(bandNo)
                    bandkey = rb.GetDescription().split(',')[0]
                    info[bandkey] = (f, bandNo, res)
                    info2[res] = (ds.RasterXSize, ds.RasterYSize)

            # find selected bands
            filenames = list()
            bandNumbers = list()
            bandKeys = list()
            pixelSizes = list()
            bandNames = list()
            wavelength = list()
            for i in bandListIndices:
                name = self.O_BAND_LIST[i].split('[')[0]
                bandKey = name.split(',')[0]
                bandKeys.append(bandKey)
                bandInfo = BAND_INFOS[bandKey]
                f, bandNo, res = info[bandKey]
                pixelSizes.append(res)
                filenames.append(f)
                bandNumbers.append([bandNo])
                bandNames.append(name)
                wavelength.append(str(bandInfo['wl_center']))

            # create band stack
            minPixelSize = min(pixelSizes)
            width, height = info2[minPixelSize]

            # create VRTs
            isVrt = filename.endswith('.vrt')
            if isVrt:
                GdalUtils.stackBands(filename, filenames, bandNumbers, width, height)
            else:
                GdalUtils.stackBands(filename + '.vrt', filenames, bandNumbers, width, height)
                RasterReader(filename + '.vrt').saveAs(filename)

            ds = gdal.Open(filename)
            ds.SetMetadata(ds10.GetMetadata())
            ds.SetMetadataItem('wavelength', '{' + ', '.join(wavelength[:ds.RasterCount]) + '}', 'ENVI')
            ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            for bandNo, name in enumerate(bandNames, 1):
                bandKey = bandKeys[bandNo - 1]
                rb: gdal.Band = ds.GetRasterBand(bandNo)
                rb.SetDescription(name)
                wl_nm = BAND_INFOS[bandKey]['wl_center']
                wl_um = wl_nm / 1000
                rb.SetMetadataItem('CENTRAL_WAVELENGTH_UM', str(wl_um), 'IMAGERY')
                scale = BAND_INFOS[bandKey]['scale']
                # rb.SetScale(0.0001)
                rb.SetScale(1 / scale)
                offset = BAND_INFOS[bandKey]['offset']
                rb.SetOffset(offset / scale)
            del ds

            # setup default renderer
            layer = QgsRasterLayer(filename)
            reader = RasterReader(layer)
            redBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['R'][0])
            greenBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['G'][0])
            blueBandNo = reader.findWavelength(CreateSpectralIndicesAlgorithm.WavebandMapping['B'][0])
            redMin, redMax = reader.provider.cumulativeCut(
                redBandNo, 0.02, 0.98, sampleSize=int(QgsRasterLayer.SAMPLE_SIZE)
            )
            greenMin, greenMax = reader.provider.cumulativeCut(
                greenBandNo, 0.02, 0.98, sampleSize=int(QgsRasterLayer.SAMPLE_SIZE)
            )
            blueMin, blueMax = reader.provider.cumulativeCut(
                blueBandNo, 0.02, 0.98, sampleSize=int(QgsRasterLayer.SAMPLE_SIZE)
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
