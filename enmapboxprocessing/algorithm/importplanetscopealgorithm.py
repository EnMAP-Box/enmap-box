from collections import defaultdict
from os.path import basename, join, dirname, abspath, exists, splitext
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
from enmapboxprocessing.algorithm.preparerasteralgorithm import PrepareRasterAlgorithm
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.gdalutils import GdalUtils
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.utils import Utils
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsRasterLayer, QgsMapLayer, \
    QgsRasterPipe, QgsRasterFileWriter


@typechecked
class ImportPlanetScopeAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Scene collection file'
    P_OUTPUT_RASTER_SR, _OUTPUT_RASTER_SR = 'outputPlanetScopeL3BRasterSR', 'Output SR raster layer'
    P_OUTPUT_RASTER_QA, _OUTPUT_RASTER_QA = 'outputPlanetScopeL3BRasterQA', 'Output UDM2 raster layer'

    def displayName(self):
        return 'Import Planet Scope L1/L3 product'

    def shortDescription(self):
        return 'Prepare a spectral raster layer from the given product. ' \
               'Wavelength information is set and data is scaled into the 0 to 1 range.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The PSScene_collection.json file associated with the product.\n'
                         'Instead of executing this algorithm, '
                         'you may drag&drop the PSScene_collection.json file directly from your system file browser '
                         'a) onto the EnMAP-Box map view area, or b) onto the Sensor Product Import panel.'),
            (self._OUTPUT_RASTER_SR, ' Surface Reflectance raster file destination.'),
            (self._OUTPUT_RASTER_QA, ' Usable Data Mask (UDM2) raster file destination.')

        ]

    def group(self):
        return Group.ImportData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='txt',
            fileFilter='Scene collection file PSScene_collection.json);;All files (*.*)'
        )
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER_SR, self._OUTPUT_RASTER_SR)
        self.addParameterVrtDestination(self.P_OUTPUT_RASTER_QA, self._OUTPUT_RASTER_QA)

    def isValidFile(self, scFilename: str) -> bool:
        if basename(scFilename) != 'PSScene_collection.json':
            return False
        data = Utils().jsonLoad(scFilename)
        for item in data['links']:
            if item['rel'] == 'item':
                clipFilename = abspath(join(dirname(scFilename), data['links'][1]['href']))
                assert exists(clipFilename)
                data2 = Utils().jsonLoad(clipFilename)
                for key in data2['assets']:
                    # if '3B_AnalyticMS' in key:
                    if 'AnalyticMS' in key:
                        return True
        return False

    def defaultParameters(self, scFilename: str):
        return {
            self.P_FILE: scFilename,
            self.P_OUTPUT_RASTER_SR: scFilename.replace('.json', '_SR.tif'),
            self.P_OUTPUT_RASTER_QA: scFilename.replace('.json', '_UDM2.vrt'),
        }

    def metadata(self, sceneJsonFilename: str) -> Tuple[Dict[str, list], Dict[str, list]]:
        data = Utils().jsonLoad(sceneJsonFilename)
        srMetadata = defaultdict(list)
        qaMetadata = defaultdict(list)
        for item in data['links']:
            if item['rel'] == 'item':
                clipFilename = abspath(join(dirname(sceneJsonFilename), item['href']))
                data2 = Utils().jsonLoad(clipFilename)

                for value in data2['assets'].values():
                    if value.get('pl:asset_type', '') in [
                        'basic_analytic_8b', 'ortho_analytic_8b', 'ortho_analytic_8b_sr'
                    ]:
                        filename = abspath(join(dirname(sceneJsonFilename), value['href']))
                        if len(srMetadata) == 0:  # take metadata from first file
                            for band in value['raster:bands']:
                                srMetadata['noDataValues'].append(band.get('nodata'))
                                srMetadata['scales'].append(band['scale'])
                            for band in value['eo:bands']:
                                srMetadata['names'].append(band['name'])
                                srMetadata['wavelengths'].append(band['center_wavelength'])
                                srMetadata['fwhms'].append(band['full_width_half_max'])
                        srMetadata['filenames'].append(filename)

                    if value.get('pl:asset_type', '') in ['basic_udm2', 'ortho_udm2']:
                        filename = abspath(join(dirname(sceneJsonFilename), value['href']))
                        if len(srMetadata) == 0:  # take metadata from first file
                            for band in value['eo:bands']:
                                qaMetadata['names'].append(f"{band['name']} - {band['description']}")
                        qaMetadata['filenames'].append(filename)
        return srMetadata, qaMetadata

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        sceneJsonFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        srFilename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER_SR, context)
        qaFilename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_RASTER_QA, context)

        with open(srFilename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            message = f'not a valid Planet Scope L3 Scene Collection file: {sceneJsonFilename}'
            if not self.isValidFile(sceneJsonFilename):
                feedback.reportError(message, True)
                raise QgsProcessingException(message)

            srMetadata, qaMetadata = self.metadata(sceneJsonFilename)

            # convert files not compatible with gdalbuildvrt (L1B product only)
            convertedFilenames = []
            for aFilename in srMetadata['filenames'] + qaMetadata['filenames']:
                ds: gdal.Dataset = gdal.Open(aFilename)
                if ds.GetSpatialRef() is None:
                    ext = splitext(aFilename)[1]
                    tifFilename = Utils().tmpFilename(srFilename, basename(aFilename).replace(ext, '.tif'))
                    feedback.pushInfo(f'convert {aFilename}')
                    layer = QgsRasterLayer(aFilename)
                    reader = RasterReader(layer)
                    provider = layer.dataProvider()
                    pipe = QgsRasterPipe()
                    pipe.set(provider.clone())
                    writer = QgsRasterFileWriter(tifFilename)
                    writer.setCreateOptions(['COMPRESS=LZW', 'INTERLEAVE=BAND'])
                    writer.writeRaster(pipe, reader.width(), reader.height(), reader.extent(), reader.crs())
                    del writer
                    ds = gdal.Open(tifFilename, gdal.GA_Update)
                    writer = RasterWriter(ds)
                    for bandNo in reader.bandNumbers():
                        writer.setNoDataValue(0, bandNo)
                    writer.close()
                    convertedFilenames.append(tifFilename)
                else:
                    convertedFilenames.append(aFilename)
            assert len(convertedFilenames) == len(srMetadata['filenames']) + len(qaMetadata['filenames'])
            srFilenames = convertedFilenames[0:len(srMetadata['filenames'])]
            qaFilenames = convertedFilenames[len(srMetadata['filenames']):]

            # create SR VRT
            isVrt = srFilename.endswith('.vrt')
            options = gdal.BuildVRTOptions()
            if isVrt:
                ds: gdal.Dataset = gdal.BuildVRT(srFilename, srFilenames, options=options)
            else:
                gdal.BuildVRT(srFilename + '.vrt', srFilenames, options=options)
                alg = PrepareRasterAlgorithm()
                parameters = {
                    alg.P_RASTER: srFilename + '.vrt',
                    alg.P_SCALE: srMetadata['scales'],
                    alg.P_DATA_TYPE: self.Float32,
                    alg.P_MONOLITHIC: False,
                    alg.P_OUTPUT_RASTER: srFilename
                }
                self.runAlg(alg, parameters, None, feedback, context, True)
                ds = gdal.Open(srFilename)

            if isVrt:
                GdalUtils().calculateDefaultHistrogram(ds, inMemory=False, feedback=feedback)

            writer = RasterWriter(ds)
            for bandNo, (name, wavelength, fwhm, scale, noDataValue) in enumerate(
                    zip(
                        srMetadata['names'], srMetadata['wavelengths'], srMetadata['fwhms'], srMetadata['scales'],
                        srMetadata['noDataValues']
                    ), 1
            ):
                writer.setBandName(name, bandNo)
                writer.setWavelength(wavelength * 1000, bandNo)
                writer.setFwhm(fwhm * 1000, bandNo)
                if isVrt:
                    writer.setScale(scale, bandNo)
                writer.setNoDataValue(noDataValue)
            writer.close()

            # - setup default renderer
            layer = QgsRasterLayer(srFilename)
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

            # create UDM2 VRT
            options = gdal.BuildVRTOptions()
            if qaFilename.endswith('.vrt'):
                ds = gdal.BuildVRT(qaFilename, qaFilenames, options=options)
            else:
                gdal.BuildVRT(qaFilename + '.vrt', qaFilenames, options=options)
                alg = SaveRasterAsAlgorithm()
                parameters = {
                    alg.P_RASTER: qaFilename + '.vrt',
                    alg.P_COPY_METADATA: False,
                    alg.P_COPY_STYLE: False,
                    alg.P_OUTPUT_RASTER: qaFilename
                }
                self.runAlg(alg, parameters, None, feedback2, context, True)
                ds = gdal.Open(qaFilename, gdal.GA_Update)
            writer = RasterWriter(ds)
            for bandNo, name in enumerate(qaMetadata['names'], 1):
                writer.setBandName(name, bandNo)
                writer.deleteNoDataValue(bandNo)
            writer.close()

            result = {
                self.P_OUTPUT_RASTER_SR: srFilename,
                self.P_OUTPUT_RASTER_QA: qaFilename,
            }
            self.toc(feedback, result)

        return result
