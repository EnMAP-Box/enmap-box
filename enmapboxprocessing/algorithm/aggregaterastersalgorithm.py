from os import makedirs
from os.path import join, exists
from typing import Dict, Any, List, Tuple

from osgeo import gdal

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.aggregaterasterbandsalgorithm import AggregateRasterBandsAlgorithm
from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
from enmapboxprocessing.algorithm.stackrasterlayersalgorithm import StackRasterLayersAlgorithm
from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.rasterwriter import RasterWriter
from processing.core.Processing import Processing
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessingException, QgsProcessing, QgsRasterLayer


@typechecked
class AggregateRastersAlgorithm(EnMAPProcessingAlgorithm):
    P_RASTERS, _RASTERS = 'rasters', 'Raster layers'
    P_FUNCTION, _FUNCTION = 'function', 'Aggregation functions'
    P_BANDWISE, _BANDWISE = 'aggregateBandWise', 'Aggregate band-wise'
    P_OUTPUT_BASENAME, _OUTPUT_BASENAME = 'outputBasename', 'Output basename'
    P_OUTPUT_FOLDER, _OUTPUT_FOLDER = 'outputFolder', 'Output folder'
    O_FUNCTION = AggregateRasterBandsAlgorithm.O_FUNCTION
    P0 = AggregateRasterBandsAlgorithm.P0

    def displayName(self) -> str:
        return 'Aggregate raster layers'

    def shortDescription(self) -> str:
        return 'Compute various aggregation functions over a list of rasters, while ignoring no data values.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._RASTERS, 'A list of raster layers with bands to be aggregated.'),
            (self._FUNCTION, 'Functions to be used.'),
            (self._BANDWISE, 'Whether to aggregate band-wise.'),
            (self._OUTPUT_BASENAME, 'The output basename used to write into the output folder. '
                                    'When using a standard name like "myRaster.tif", all outputs are written into a '
                                    'single file. When using a pattern like "myRaster_{function}.tif", the different '
                                    'types of aggregations are written into individual files.'),
            (self._OUTPUT_FOLDER, self.FolderDestination)
        ]

    def group(self):
        return Group.RasterAnalysis.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterMultipleLayers(self.P_RASTERS, self._RASTERS, QgsProcessing.SourceType.TypeRaster)
        self.addParameterEnum(self.P_FUNCTION, self._FUNCTION, self.O_FUNCTION, True, None)
        self.addParameterBoolean(self.P_BANDWISE, self._BANDWISE, True, True)
        self.addParameterString(self.P_OUTPUT_BASENAME, self._OUTPUT_BASENAME)
        self.addParameterFolderDestination(self.P_OUTPUT_FOLDER, self._OUTPUT_FOLDER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        rasters: List[QgsRasterLayer] = self.parameterAsLayerList(parameters, self.P_RASTERS, context)
        functionIndices = self.parameterAsEnums(parameters, self.P_FUNCTION, context)
        aggregateBandWise = self.parameterAsBoolean(parameters, self.P_BANDWISE, context)
        basename = self.parameterAsString(parameters, self.P_OUTPUT_BASENAME, context)
        writeFunctionWise = '{function}' in basename
        foldername = self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context)
        tmpfoldername = join(foldername, 'tmp')
        if not exists(tmpfoldername):
            makedirs(tmpfoldername)
        logfilename = join(tmpfoldername, basename.replace('{function}', '') + '.log')

        with open(logfilename, 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            if aggregateBandWise:
                for raster in rasters:
                    if raster.bandCount() != rasters[0].bandCount():
                        raise QgsProcessingException(
                            f'Number of raster bands do not match.\n{rasters[0].source()}\n{raster.source()} '
                        )

                # stack and aggregate band-wise
                filenames = list()
                for bandNo in range(1, rasters[0].bandCount() + 1):
                    alg1 = StackRasterLayersAlgorithm()
                    parameters1 = {
                        alg1.P_RASTERS: rasters,
                        alg1.P_BAND: bandNo,
                        alg1.P_OUTPUT_RASTER: join(tmpfoldername, f'band_{bandNo}.vrt')
                    }
                    Processing.runAlgorithm(alg1, parameters1, None, feedback2, context)

                    alg2 = AggregateRasterBandsAlgorithm()
                    parameters = {
                        alg2.P_RASTER: parameters1[alg1.P_OUTPUT_RASTER],
                        alg2.P_FUNCTION: functionIndices,
                        alg2.P_OUTPUT_RASTER: join(tmpfoldername, f'aggregation_{bandNo}.tif')
                    }
                    Processing.runAlgorithm(alg2, parameters, None, feedback2, context)
                    filenames.append(parameters[alg2.P_OUTPUT_RASTER])

                if writeFunctionWise:
                    for bandNo, functionIndex in enumerate(functionIndices, 1):
                        # all band for current function
                        alg1 = StackRasterLayersAlgorithm()
                        parameters1 = {
                            alg1.P_RASTERS: filenames,
                            alg1.P_BAND: bandNo,
                            alg1.P_OUTPUT_RASTER: join(
                                tmpfoldername,
                                basename.replace('{function}', self.O_FUNCTION[functionIndex]).replace(' ', '_')
                            ) + '.vrt'

                        }
                        Processing.runAlgorithm(alg1, parameters1, None, feedback2, context)

                        reader = RasterReader(rasters[0])
                        ds: gdal.Dataset = gdal.Open(parameters1[alg2.P_OUTPUT_RASTER], gdal.GA_Update)
                        writer = RasterWriter(ds)
                        for bandNo in reader.bandNumbers():
                            writer.setBandName(reader.bandName(bandNo), bandNo)
                        writer.close()
                        del ds

                        alg2 = SaveRasterAsAlgorithm()
                        parameters2 = {
                            alg2.P_RASTER: parameters1[alg1.P_OUTPUT_RASTER],
                            alg2.P_COPY_STYLE: False,
                            alg2.P_COPY_METADATA: False,
                            alg2.P_OUTPUT_RASTER: join(
                                foldername,
                                basename.replace('{function}', self.O_FUNCTION[functionIndex].replace(' ', '_'))
                            )
                        }
                        Processing.runAlgorithm(alg2, parameters2, None, feedback2, context)

                else:

                    alg1 = StackRasterLayersAlgorithm()
                    parameters1 = {
                        alg1.P_RASTERS: filenames,
                        alg1.P_OUTPUT_RASTER: join(tmpfoldername, basename) + '.vrt'
                    }
                    Processing.runAlgorithm(alg1, parameters1, None, feedback2, context)

                    reader = RasterReader(rasters[0])
                    ds: gdal.Dataset = gdal.Open(parameters1[alg2.P_OUTPUT_RASTER], gdal.GA_Update)
                    writer = RasterWriter(ds)
                    bandNo = 1
                    for bandNo2 in reader.bandNumbers():
                        for functionIndex in functionIndices:
                            writer.setBandName(reader.bandName(bandNo2) + ' - ' + self.O_FUNCTION[functionIndex],
                                               bandNo)
                            bandNo += 1
                    writer.close()
                    del ds

                    alg2 = SaveRasterAsAlgorithm()
                    parameters2 = {
                        alg2.P_RASTER: parameters1[alg1.P_OUTPUT_RASTER],
                        alg2.P_COPY_STYLE: False,
                        alg2.P_COPY_METADATA: False,
                        alg2.P_OUTPUT_RASTER: join(foldername, basename)
                    }
                    Processing.runAlgorithm(alg2, parameters2, None, feedback2, context)
            else:
                # stack and aggregate all bands
                alg1 = StackRasterLayersAlgorithm()
                parameters1 = {
                    alg1.P_RASTERS: rasters,
                    alg1.P_OUTPUT_RASTER: join(tmpfoldername, 'bands.vrt')
                }
                Processing.runAlgorithm(alg1, parameters1, None, feedback2, context)

                alg2 = AggregateRasterBandsAlgorithm()
                parameters2 = {
                    alg2.P_RASTER: parameters1[alg1.P_OUTPUT_RASTER],
                    alg2.P_FUNCTION: functionIndices,
                    alg2.P_OUTPUT_RASTER: join(tmpfoldername, 'aggregation.tif')
                }
                Processing.runAlgorithm(alg2, parameters2, None, feedback2, context)

                if writeFunctionWise:
                    for bandNo, functionIndex in enumerate(functionIndices, 1):
                        alg3 = TranslateRasterAlgorithm()
                        parameters3 = {
                            alg3.P_RASTER: parameters2[alg1.P_OUTPUT_RASTER],
                            alg3.P_BAND_LIST: [bandNo],
                            alg3.P_COPY_STYLE: False,
                            alg3.P_COPY_METADATA: False,
                            alg3.P_OUTPUT_RASTER: join(
                                foldername,
                                basename.replace('{function}', self.O_FUNCTION[functionIndex].replace(' ', '_'))
                            )
                        }
                        Processing.runAlgorithm(alg3, parameters3, None, feedback2, context)
                else:
                    alg3 = TranslateRasterAlgorithm()
                    parameters3 = {
                        alg3.P_RASTER: parameters2[alg1.P_OUTPUT_RASTER],
                        alg3.P_COPY_STYLE: False,
                        alg3.P_COPY_METADATA: False,
                        alg3.P_OUTPUT_RASTER: join(foldername, basename)
                    }
                    Processing.runAlgorithm(alg3, parameters3, None, feedback2, context)

            result = {self.P_OUTPUT_FOLDER: foldername}
            self.toc(feedback, result)

        return result
