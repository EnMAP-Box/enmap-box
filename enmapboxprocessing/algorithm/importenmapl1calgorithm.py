from os.path import basename
from typing import Dict, Any, List, Tuple
from xml.etree import ElementTree

from osgeo import gdal

from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.gdalutils import GdalUtils
from qgis.core import (QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException)
from enmapbox.typeguard import typechecked


@typechecked
class ImportEnmapL1CAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputEnmapL1CRaster', 'Output raster layer'

    def displayName(self):
        return 'Import EnMAP L1C product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled according to data gain/offset values.'

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
            self.P_FILE, self._FILE, extension='XML', fileFilter='Metadata file (*-METADATA.XML);;All files (*.*)'
        )
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER)

    def isValidFile(self, file: str) -> bool:
        return basename(file).startswith('ENMAP') & \
               basename(file).endswith('METADATA.XML') & \
               ('L1C' in basename(file))

    def defaultParameters(self, xmlFilename: str):
        return {
            self.P_FILE: xmlFilename,
            self.P_OUTPUT_RASTER: xmlFilename.replace('METADATA.XML', 'SPECTRAL_IMAGE.vrt'),
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
            # e.g. 'ENMAP01-____L1C-DT000326721_20170626T102020Z_001_V000204_20200406T180016Z-METADATA.XML'
            if not self.isValidFile(xmlFilename):
                message = f'not a valid EnMAP L1C product: {xmlFilename}'
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
            ds = gdal.Open(ImportEnmapL1BAlgorithm.findFilename(
                xmlFilename.replace('-METADATA.XML', '-SPECTRAL_IMAGE'))
            )
            ds: gdal.Dataset = gdal.Translate(filename, ds)
            ds.SetMetadataItem('wavelength', '{' + ', '.join(wavelength[:ds.RasterCount]) + '}', 'ENVI')
            ds.SetMetadataItem('wavelength_units', 'nanometers', 'ENVI')
            ds.SetMetadataItem('fwhm', '{' + ', '.join(fwhm[:ds.RasterCount]) + '}', 'ENVI')

            GdalUtils().calculateDefaultHistrogram(ds, inMemory=False, feedback=feedback)

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
