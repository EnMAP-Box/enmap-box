from os.path import basename
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.gdalutils import GdalUtils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException


@typechecked
class ImportDesisL1CAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputDesisL1CRaster', 'Output raster layer'

    def displayName(self):
        return 'Import DESIS L1C product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled according to data gain/offset values.\n' \
               'Note that the DESIS L1C spectral data file is band interleaved by pixel and compressed, ' \
               'which is very disadvantageous for visualization in QGIS / EnMAP-Box. ' \
               'For faster exploration concider saving the resulting VRT raster layer as GTiff format ' \
               'via the "Translate raster layer" algorithm.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The metadata XML file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the metadata XML file directly from your system file browser '
                         'a) onto the EnMAP-Box map view area, or b) onto the Sensor Product Import panel.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='xml', fileFilter='Metadata file (*-METADATA.xml);;All files (*.*)'
        )
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('DESIS-HSI-L1C') & basename(file).endswith('METADATA.xml')

    def defaultParameters(self, xmlFilename: str):
        return {
            self.P_FILE: xmlFilename,
            self.P_OUTPUT_RASTER: xmlFilename.replace('METADATA.xml', 'SPECTRAL_IMAGE.vrt'),
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        xmlFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210-METADATA.xml'
            if not self.isValidFile(xmlFilename):
                message = f'not a valid DESIS L1C product: {xmlFilename}'
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            # read metadata
            with open(xmlFilename.replace('-METADATA.xml', '-SPECTRAL_IMAGE.hdr')) as file:
                text = file.read()
            text = text.replace('  ', ' ')

            def getMetadataAsString(key, text):
                i1 = text.index(key + ' = {')
                i2 = text.index('}', i1)
                value = text[i1 + len(key) + 3:i2 + 1].replace('\n', '')
                return value

            def getMetadataAsList(key, text):
                text = getMetadataAsString(key, text)
                values = text.replace('{', '').replace('}', '').split(',')
                return values

            wavelength = getMetadataAsList('wavelength', text)
            fwhm = getMetadataAsList('fwhm', text)
            gains = getMetadataAsList('data gain values', text)
            offsets = getMetadataAsList('data offset values', text)

            # create VRTs
            ds = gdal.Open(xmlFilename.replace('-METADATA.xml', '-SPECTRAL_IMAGE.tif'))
            ds: gdal.Dataset = gdal.Translate(filename, ds)
            ds.SetMetadataItem('wavelength', '{' + ', '.join(wavelength[:ds.RasterCount]) + '}', 'ENVI')
            ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            ds.SetMetadataItem('fwhm', '{' + ', '.join(fwhm[:ds.RasterCount]) + '}', 'ENVI')
            rasterBands = [ds.GetRasterBand(i + 1) for i in range(ds.RasterCount)]
            rasterBand: gdal.Band
            for i, rasterBand in enumerate(rasterBands):
                rasterBand.SetDescription(f'band {i + 1} ({wavelength[i]} Nanometers)')
                rasterBand.SetScale(float(gains[i]))
                rasterBand.SetOffset(float(offsets[i]))
                rasterBand.FlushCache()

            GdalUtils().calculateDefaultHistrogram(ds, inMemory=True, feedback=feedback)

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
