import zipfile
from os.path import basename, splitext, dirname, join
from typing import Dict, Any, List, Tuple

from defusedxml import ElementTree
from osgeo import gdal
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsRasterLayer, QgsMapLayer

from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils


class ImportIperliteL1CAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata XML file or ZIP file'
    P_OUTPUT_RASTER, _OUTPUT_RASTER = 'outputIperliteL2CRaster', 'Output raster layer'

    def displayName(self):
        return 'Import IPERLITE L1C product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength and FWHM information is set and data is scaled into the 0 to 1 range.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The metadata XML file or the ZIP file associated with the product.\n'),
            (self._OUTPUT_RASTER, self.RasterFileDestination)
        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='XML',
            fileFilter='Metadata or ZIP file (*.XML *.ZIP);;All files (*.*)'
        )
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER, self._OUTPUT_RASTER, vrtOnly=True)

    def isValidFile(self, file: str) -> bool:
        isValid = basename(file).startswith('IPERLITE_LEVEL1C')
        isValid &= basename(file).endswith('.xml') or file.lower().endswith('.zip')
        return isValid

    def defaultParameters(self, xmlOrZipFilename: str):
        if xmlOrZipFilename.lower().endswith('.zip'):
            raise NotImplementedError()
        filename = xmlOrZipFilename
        filename = filename.replace('METADATA.xml', '-SPECTRAL_IMAGE.vrt')
        return {
            self.P_FILE: xmlOrZipFilename,
            self.P_OUTPUT_RASTER: filename
        }

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        xmlOrZipFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # check filename
            # e.g. 'IPERLITE_LEVEL1C_20260915T140722Z_20260915T140737Z_WGS84_20M_V001.xml'
            if not self.isValidFile(xmlOrZipFilename):
                message = (f'not a valid IPERLITE L1C product: {xmlOrZipFilename}')
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            # read metadata
            isZip = xmlOrZipFilename.lower().endswith('.zip')
            if isZip:
                with zipfile.ZipFile(xmlOrZipFilename) as z:
                    productName = splitext(basename(xmlOrZipFilename))[0]
                    with z.open(productName + '/' + productName + '.xml') as f:
                        tree = ElementTree.parse(f)
                        root = tree.getroot()
                productRoot = '/vsizip/' + xmlOrZipFilename + '/' + productName
            else:
                root = ElementTree.parse(xmlOrZipFilename).getroot()
                productRoot = dirname(xmlOrZipFilename)

            wavelength = [float(item.text) for item in root.findall('.//CENTRAL_WAVELENGTH_NM')]
            fwhm = [float(item.text) for item in root.findall('.//FWHM')]
            dataFilePath = [join(productRoot, item.get("href")).replace('\\', '/')
                            for item in root.findall('.//DATA_FILE_PATH')
                            if 'RTOA#' in item.get("href")]

            # build band stack
            if splitext(filename)[1].lower() == '.vrt':
                options = gdal.BuildVRTOptions(separate=True)
                gdal.BuildVRT(filename, dataFilePath, options=options)
            else:
                raise NotImplementedError()

            ds = gdal.Open(filename)
            writer = RasterWriter(ds)
            for bandNo in writer.bandNumbers():
                writer.setBandName(f'band {bandNo} ({wavelength[bandNo - 1]} Nanometers)', bandNo)
                # writer.setScale(float(gains[bandNo - 1]), bandNo)
                # writer.setOffset(float(offsets[bandNo - 1]), bandNo)
                writer.setFwhm(fwhm[bandNo - 1], bandNo)
                writer.setWavelength(wavelength[bandNo - 1], bandNo)
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
