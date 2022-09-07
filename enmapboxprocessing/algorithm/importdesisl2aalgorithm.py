from os.path import basename
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from typeguard import typechecked


@typechecked
class ImportDesisL2AAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputDesisL2ARaster', 'Output raster layer'

    def displayName(self):
        return 'Import DESIS L2A product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled into the 0 to 10000 range.\n' \
               'Note that the DESIS L2D spectral data file is band interleaved by pixel and compressed, ' \
               'which is very disadvantageous for visualization in QGIS / EnMAP-Box. ' \
               'For faster exploration concider saving the resulting VRT raster layer as GTiff format ' \
               'via the "Translate raster layer" algorithm.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The metadata XML file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the metadata XML file directly from your system file browser onto '
                         'the EnMAP-Box map view area.'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.Test.value + Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_FILE, self._FILE, extension='xml')
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('DESIS-HSI-L2A') & basename(file).endswith('METADATA.xml')

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
            # e.g. 'DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210-METADATA.xml'
            if not self.isValidFile(xmlFilename):
                message = f'not a valid DESIS L2A product: {xmlFilename}'
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

            wavelength = getMetadataAsString('wavelength', text)
            fwhm = getMetadataAsString('fwhm', text)
            gains = getMetadataAsList('data gain values', text)
            offsets = getMetadataAsList('data offset values', text)

            # create VRTs
            ds = gdal.Open(xmlFilename.replace('-METADATA.xml', '-SPECTRAL_IMAGE.TIF'))
            options = gdal.TranslateOptions(format='VRT', outputType=gdal.GDT_Int16)
            ds: gdal.Dataset = gdal.Translate(destName=filename, srcDS=ds, options=options)
            ds.SetMetadataItem('wavelength', wavelength, 'ENVI')
            ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            ds.SetMetadataItem('fwhm', fwhm, 'ENVI')
            rasterBands = [ds.GetRasterBand(i + 1) for i in range(ds.RasterCount)]
            rasterBand: gdal.Band
            wavelength = wavelength[1:-1].split(',')
            for i, rasterBand in enumerate(rasterBands):
                rasterBand.SetDescription(f'band {i + 1} ({wavelength[i]} Nanometers)')
                rasterBand.SetScale(float(gains[i]) * 1e4)
                rasterBand.SetOffset(float(offsets[i]))
                rasterBand.FlushCache()

            result = {self.P_OUTPUT_RASTER: filename}
            self.toc(feedback, result)

        return result
