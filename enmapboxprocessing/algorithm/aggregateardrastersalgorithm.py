import fnmatch
from os import listdir
from os.path import join, isdir, isfile
from typing import Dict, Any, List, Tuple

from processing.core.Processing import Processing
from qgis.core import QgsProcessingParameterFile, QgsProcessingContext, QgsProcessingFeedback

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.aggregaterasterbandsalgorithm import AggregateRasterBandsAlgorithm
from enmapboxprocessing.algorithm.aggregaterastersalgorithm import AggregateRastersAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.rasterreader import RasterReader


@typechecked
class AggregateArdRastersAlgorithm(EnMAPProcessingAlgorithm):
    P_DATA_CUBE, _DATA_CUBE = 'dataCube', 'Data cube'
    P_TILE_FILTER, _TILE_FILTER = 'tileFilter', 'Tile filter'
    P_BASENAME_FILTER, _BASENAME_FILTER = 'basenameFilter', 'Basename filter'
    P_FUNCTION, _FUNCTION = 'function', 'Aggregation functions'

    P_EXTERNAL_MASK, _EXTERNAL_MASK = 'externalMask', 'External mask'
    P_START_DATE, _START_DATE = 'startDate', 'Start date'
    P_END_DATE, _END_DATE = 'endDate', 'End date'
    P_START_DAY, _START_DAY = 'startDay', 'Start day'
    P_END_DAY, _END_DAY = 'endDay', 'End day'

    P_OUTPUT_BASENAME, _OUTPUT_BASENAME = 'outputBasename', 'Output basename'
    P_OUTPUT_DATA_CUBE, _OUTPUT_DATA_CUBE = 'outputDataCube', 'Output data cube'
    O_FUNCTION = AggregateRasterBandsAlgorithm.O_FUNCTION

    def displayName(self) -> str:
        return 'Aggregate ARD raster layers'

    def shortDescription(self) -> str:
        return ('Compute various aggregation functions over a list of analysis ready (ARD) rasters in a data cube, '
                'while ignoring no data values.\n'
                'The computation is performed individually for each tile of the data cube.')

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATA_CUBE, 'A data cube with raster layers to be aggregated.'),
            (self._TILE_FILTER, 'List of tiles to be processed. If not specified, all tiles are used.'),
            (self._BASENAME_FILTER, 'A wildcard pattern for matching raster layers to be used.'),
            (self._FUNCTION, 'Aggregation functions to be used.'),

            (self._EXTERNAL_MASK, r'A matching pattern for specifying external masks using the tile name {tile}, '
                                  r'the file basename {basename} and the file extension {ext} of the current raster. '
                                  'Possible patterns are:\n'
                                  r'i) absolute path like c:\dataCube\{tile}\{basename}.{ext}'
                                  r'ii) relative path like mask\{basename}.{ext} or {basename}.mask.{ext}'),
            (self._START_DATE, 'Filter rasters by start date.'),
            (self._END_DATE, 'Filter rasters by end date.'),
            (self._START_DAY, 'Filter rasters by start day.'),
            (self._END_DAY, 'Filter rasters by end day.'),

            (self._OUTPUT_BASENAME, 'The output basename used to write into the output data cube. '
                                    'When using a standard name like "myRaster.tif", all outputs are written into a '
                                    'single file. When using a pattern like "myRaster_{function}.tif", the different '
                                    'types of aggregations are written into individual files.'),
            (self._OUTPUT_DATA_CUBE, self.DataCubeDestination)
        ]

    def group(self):
        return Group.AnalysisReadyData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(self.P_DATA_CUBE, self._DATA_CUBE, QgsProcessingParameterFile.Behavior.Folder)
        self.addParameterMatrix(self.P_TILE_FILTER, self._TILE_FILTER, 1, False, ['Tile name'], None, True, True)
        self.addParameterString(self.P_BASENAME_FILTER, self._BASENAME_FILTER, )
        self.addParameterEnum(self.P_FUNCTION, self._FUNCTION, self.O_FUNCTION, True, None)
        self.addParameterString(self.P_EXTERNAL_MASK, self._EXTERNAL_MASK, None, False, True, True)
        self.addParameterDate(self.P_START_DATE, self._START_DATE, None, True, advanced=True)
        self.addParameterDate(self.P_END_DATE, self._END_DATE, None, True, advanced=True)
        self.addParameterInt(self.P_START_DAY, self._START_DAY, None, True, 1, 366, True)
        self.addParameterInt(self.P_END_DAY, self._END_DAY, None, True, 1, 366, True)
        self.addParameterString(self.P_OUTPUT_BASENAME, self._OUTPUT_BASENAME)
        self.addParameterFolderDestination(self.P_OUTPUT_DATA_CUBE, self._OUTPUT_DATA_CUBE)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        dataCube = self.parameterAsFile(parameters, self.P_DATA_CUBE, context)
        tileFilter = self.parameterAsMatrix(parameters, self.P_TILE_FILTER, context)
        baseNameFilter = self.parameterAsString(parameters, self.P_BASENAME_FILTER, context)
        functionIndices = self.parameterAsEnums(parameters, self.P_FUNCTION, context)
        externalMask = self.parameterAsString(parameters, self.P_EXTERNAL_MASK, context)
        startDate = self.parameterAsDateTime(parameters, self.P_START_DATE, context).date()
        endDate = self.parameterAsDateTime(parameters, self.P_END_DATE, context).date()
        startDay = self.parameterAsInt(parameters, self.P_START_DAY, context)
        endDay = self.parameterAsInt(parameters, self.P_END_DAY, context)
        outputBasename = self.parameterAsString(parameters, self.P_OUTPUT_BASENAME, context)
        outputDataCube = self.parameterAsFileOutput(parameters, self.P_OUTPUT_DATA_CUBE, context)

        feedback.pushInfo('Loop over tiles')
        for tilename in listdir(dataCube):
            if not isdir(join(dataCube, tilename)):
                continue

            if tileFilter is not None:
                if tilename not in tileFilter:
                    continue

            feedback.pushInfo('  ' + tilename)

            filenames = list()
            for basename in listdir(join(dataCube, tilename)):
                filename = join(dataCube, tilename, basename)
                if not isfile(filename):
                    continue

                if not fnmatch.fnmatch(basename, baseNameFilter):
                    continue

                reader = RasterReader(filename)
                date = reader.centerTime()
                if date is None:
                    if startDate.isValid() or endDate.isValid() or startDay is not None or endDay is not None:
                        continue
                else:
                    date = date.date()

                    if date.dayOfYear() < startDay or date.dayOfYear() > endDay:
                        raise NotImplementedError()

                    if date < startDate or date > endDate:
                        continue

                feedback.pushInfo(f'    {filename} [{date}]')

                filenames.append(filename)

            if len(filenames) == 0:
                continue

            alg = AggregateRastersAlgorithm()
            parameters = {
                alg.P_RASTERS: filenames,
                alg.P_FUNCTION: functionIndices,
                alg.P_OUTPUT_BASENAME: outputBasename,
                alg.P_OUTPUT_FOLDER: join(outputDataCube, tilename)
            }
            Processing.runAlgorithm(alg, parameters, None, feedback, context)

        result = {self.P_OUTPUT_DATA_CUBE: outputDataCube}

        return result
