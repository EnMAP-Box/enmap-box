from os.path import basename, exists
from typing import Dict, Any, List, Tuple
from xml.etree import ElementTree

from osgeo import gdal

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.gdalutils import GdalUtils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from enmapbox.typeguard import typechecked


@typechecked
class ImportEnmapL1BAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_OUTPUT_VNIR_RASTER, _OUTPUT_VNIR_RASTER = 'outputEnmapL1BRasterVnir', 'Output VNIR raster layer'
    P_OUTPUT_SWIR_RASTER, _OUTPUT_SWIR_RASTER = 'outputEnmapL1BRasterSwir', 'Output SWIR raster layer'

    def displayName(self):
        return 'Import EnMAP L1B product'

    def shortDescription(self):
        return 'Prepare VNIR and SWIR spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled according to data gain/offset values.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The metadata XML file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the metadata XML file directly from your system file browser '
                         'a) onto the EnMAP-Box map view area, or b) onto the Sensor Product Import panel.'),
            (self._OUTPUT_VNIR_RASTER, self.RasterFileDestination),
            (self._OUTPUT_SWIR_RASTER, self.RasterFileDestination),
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='XML', fileFilter='Metadata file (*-METADATA.XML);;All files (*.*)'
        )
        self.addParameterVrtDestination(self.P_OUTPUT_VNIR_RASTER, self._OUTPUT_VNIR_RASTER)
        self.addParameterVrtDestination(self.P_OUTPUT_SWIR_RASTER, self._OUTPUT_SWIR_RASTER)

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('ENMAP') & \
               basename(file).endswith('METADATA.XML') & \
               ('L1B' in basename(file))

    def defaultParameters(self, xmlFilename: str):
        return {
            self.P_FILE: xmlFilename,
            self.P_OUTPUT_VNIR_RASTER: xmlFilename.replace('METADATA.XML', 'SPECTRAL_IMAGE_VNIR.vrt'),
            self.P_OUTPUT_SWIR_RASTER: xmlFilename.replace('METADATA.XML', 'SPECTRAL_IMAGE_SWIR.vrt'),
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        xmlFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        filename1 = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_VNIR_RASTER, context)
        filename2 = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_SWIR_RASTER, context)

        with open(filename1 + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'ENMAP01-____L1B-DT000400126_20170218T110119Z_003_V000204_20200508T124425Z-METADATA.XML'
            if not self.isValidFile(xmlFilename):
                message = f'not a valid EnMAP L1B product: {xmlFilename}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            # read metadata
            root = ElementTree.parse(xmlFilename).getroot()
            wavelength = [item.text for item in
                          root.findall('specific/bandCharacterisation/bandID/wavelengthCenterOfBand')]
            fwhm = [item.text for item in root.findall('specific/bandCharacterisation/bandID/FWHMOfBand')]
            gains = [item.text for item in root.findall('specific/bandCharacterisation/bandID/GainOfBand')]
            offsets = [item.text for item in root.findall('specific/bandCharacterisation/bandID/OffsetOfBand')]

            # create VRTs
            ds = gdal.Open(self.findFilename(xmlFilename.replace('-METADATA.XML', '-SPECTRAL_IMAGE_VNIR')))
            dsVnir: gdal.Dataset = gdal.Translate(filename1, ds)
            dsVnir.SetMetadataItem('wavelength', '{' + ', '.join(wavelength[:dsVnir.RasterCount]) + '}', 'ENVI')
            dsVnir.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            dsVnir.SetMetadataItem('fwhm', '{' + ', '.join(fwhm[:dsVnir.RasterCount]) + '}', 'ENVI')

            ds = gdal.Open(self.findFilename(xmlFilename.replace('-METADATA.XML', '-SPECTRAL_IMAGE_SWIR')))
            dsSwir: gdal.Dataset = gdal.Translate(filename2, ds)
            dsSwir.SetMetadataItem('wavelength', '{' + ', '.join(wavelength[dsVnir.RasterCount:]) + '}', 'ENVI')
            dsSwir.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            dsSwir.SetMetadataItem('fwhm', '{' + ', '.join(fwhm[dsVnir.RasterCount:]) + '}', 'ENVI')

            rasterBands = list()
            rasterBands.extend(dsVnir.GetRasterBand(i + 1) for i in range(dsVnir.RasterCount))
            rasterBands.extend(dsSwir.GetRasterBand(i + 1) for i in range(dsSwir.RasterCount))
            rasterBand: gdal.Band
            for i, rasterBand in enumerate(rasterBands):
                rasterBand.SetDescription(f'band {i + 1} ({wavelength[i]} Nanometers)')
                rasterBand.SetScale(float(gains[i]))
                rasterBand.SetOffset(float(offsets[i]))
                rasterBand.FlushCache()

            # fix wrong GeoTransform tuple
            geoTransform = dsVnir.GetGeoTransform()
            geoTransform = geoTransform[:-1] + (-abs(geoTransform[-1]),)
            dsVnir.SetGeoTransform(geoTransform)
            geoTransform = dsSwir.GetGeoTransform()
            geoTransform = geoTransform[:-1] + (-abs(geoTransform[-1]),)
            dsSwir.SetGeoTransform(geoTransform)

            GdalUtils().calculateDefaultHistrogram(dsVnir, inMemory=False, feedback=feedback)
            GdalUtils().calculateDefaultHistrogram(dsSwir, inMemory=False, feedback=feedback)

            result = {self.P_OUTPUT_VNIR_RASTER: filename1, self.P_OUTPUT_SWIR_RASTER: filename2}
            self.toc(feedback, result)

        return result

    @staticmethod
    def findFilename(basename: str):
        extensions = ['.TIF', '.GEOTIFF', '.BSQ', '.BIL', '.BIP', 'JPEG2000', '.JP2', '.jp2', '_COG.tiff']
        for extention in extensions:
            filename = basename + extention
            if exists(filename):
                return filename
        raise QgsProcessingException(f'Spectral cube not found: {basename}')
