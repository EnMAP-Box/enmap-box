import random
import string
from os import makedirs
from os.path import join, basename, exists
from typing import Dict, Any, List, Tuple

from qgis.core import QgsProcessing, QgsProcessingParameterField, QgsProcessingContext, \
    QgsProcessingFeedback

from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.importenmapl1balgorithm import ImportEnmapL1BAlgorithm
from enmapboxprocessing.algorithm.importenmapl2aalgorithm import ImportEnmapL2AAlgorithm
from enmapboxprocessing.algorithm.tilerasteralgorithm import TileRasterAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group


@typechecked
class TileEnmapL2AAlgorithm(EnMAPProcessingAlgorithm):
    P_FILE, _FILE = 'file', 'Metadata file'
    P_TILING_SCHEME, _TILING_SCHEME = 'tilingScheme', 'Tiling scheme'
    P_TILE_NAMES, _TILE_NAMES = 'tileNames', 'Tile names'
    P_RESOLUTION, _RESOLUTION = 'resolution', 'Pixel resolution'
    P_SET_BAD_BANDS, _SET_BAD_BANDS = 'setBadBands', 'Set bad bands'
    P_EXCLUDE_BAD_BANDS, _EXCLUDE_BAD_BANDS, = 'excludeBadBands', 'Exclude bad bands'
    P_DETECTOR_OVERLAP, _DETECTOR_OVERLAP = 'detectorOverlap', 'Detector overlap region'
    P_OUTPUT_BASENAME, _OUTPUT_BASENAME = 'outputBasename', 'Output basename'
    P_OUTPUT_FOLDER, _OUTPUT_FOLDER = 'outputFolder', 'Output folder'

    def displayName(self):
        return 'Tile EnMAP L2A product'

    def shortDescription(self):
        return 'Tile EnMAP L2A product into given tiling scheme.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._FILE, 'The metadata XML file associated with the product.\n'),
            (self._TILING_SCHEME, 'Tiling scheme to be applied.'),
            (self._TILE_NAMES, 'Field with tile names.'),
            (self._RESOLUTION, 'Output pixel resolution.'),
            (self._SET_BAD_BANDS, 'Whether to mark no data bands as bad bands.'),
            (self._EXCLUDE_BAD_BANDS, 'Whether to exclude bands.'),
            (self._DETECTOR_OVERLAP, 'Different options for handling the detector overlap region from 900 to 1000 '
                                     'nanometers. For the Moving average filter, a kernel size of 3 is used.'),
            (self._OUTPUT_BASENAME, 'Output basename. If not specified, the original basename is used.'),
            (self._OUTPUT_FOLDER, self.FolderDestination)
        ]

    def group(self):
        return Group.AnalysisReadyData.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterFile(
            self.P_FILE, self._FILE, extension='XML', fileFilter='Metadata file (*-METADATA.XML);;All files (*.*)'
        )
        self.addParameterVectorLayer(
            self.P_TILING_SCHEME, self._TILING_SCHEME, (QgsProcessing.SourceType.TypeVectorPolygon,)
        )
        self.addParameterField(
            self.P_TILE_NAMES, self._TILE_NAMES, None, self.P_TILING_SCHEME,
            QgsProcessingParameterField.DataType.String
        )
        self.addParameterFloat(self.P_RESOLUTION, self._RESOLUTION, None, True, None, None, True)
        self.addParameterBoolean(self.P_SET_BAD_BANDS, self._SET_BAD_BANDS, True, True)
        self.addParameterBoolean(self.P_EXCLUDE_BAD_BANDS, self._EXCLUDE_BAD_BANDS, True, True)
        self.addParameterEnum(
            self.P_DETECTOR_OVERLAP, self._DETECTOR_OVERLAP, ImportEnmapL2AAlgorithm.O_DETECTOR_OVERLAP, False,
            ImportEnmapL2AAlgorithm.SwirOnlyOverlapOption
        )
        self.addParameterString(self.P_OUTPUT_BASENAME, self._OUTPUT_BASENAME, None, False, True)
        self.addParameterFolderDestination(self.P_OUTPUT_FOLDER, self._OUTPUT_FOLDER)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:

        xmlFilename = self.parameterAsFile(parameters, self.P_FILE, context)
        setBadBands = self.parameterAsBoolean(parameters, self.P_SET_BAD_BANDS, context)
        excludeBadBands = self.parameterAsBoolean(parameters, self.P_EXCLUDE_BAD_BANDS, context)
        detectorOverlap = self.parameterAsEnum(parameters, self.P_DETECTOR_OVERLAP, context)

        tilingScheme = self.parameterAsVectorLayer(parameters, self.P_TILING_SCHEME, context)
        tileNameField = self.parameterAsField(parameters, self.P_TILE_NAMES, context)
        resolution = self.parameterAsFloat(parameters, self.P_RESOLUTION, context)
        baseName = self.parameterAsString(parameters, self.P_OUTPUT_BASENAME, context)
        folderName = self.parameterAsFileOutput(parameters, self.P_OUTPUT_FOLDER, context)

        if baseName is None:
            baseName = basename(xmlFilename.replace('-METADATA.XML', ''))

        def id_generator(size=40, chars=string.ascii_uppercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

        tmpFolderName = join(folderName, '_tmp', id_generator())
        if not exists(tmpFolderName):
            makedirs(tmpFolderName)
        logFileName = join(tmpFolderName, baseName + '.log')

        with open(logFileName, 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            # import product
            filenameSpectral = join(tmpFolderName, 'product', 'SPECTRAL_IMAGE.tif')
            alg = ImportEnmapL2AAlgorithm()
            parameters = {
                alg.P_FILE: xmlFilename,
                alg.P_SET_BAD_BANDS: setBadBands,
                alg.P_EXCLUDE_BAD_BANDS: excludeBadBands,
                alg.P_DETECTOR_OVERLAP: detectorOverlap,
                alg.P_OUTPUT_RASTER: filenameSpectral
            }
            self.runAlg(alg, parameters, None, feedback2, context, True)

            # tile product
            alg = TileRasterAlgorithm()
            parameters = {
                alg.P_TILE_NAMES: tileNameField,
                alg.P_TILING_SCHEME: tilingScheme,
                alg.P_RESOLUTION: resolution,
                alg.P_OUTPUT_FOLDER: folderName
            }

            subdatasets = [
                (
                    filenameSpectral,
                    baseName + '-SPECTRAL_IMAGE.tif',
                    None
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(xmlFilename.replace('-METADATA.XML', '-QL_PIXELMASK')),
                    baseName + '-QL_PIXELMASK.tif',
                    255
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(xmlFilename.replace('-METADATA.XML', '-QL_QUALITY_CIRRUS')),
                    baseName + '-QL_QUALITY_CIRRUS.tif',
                    255
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(xmlFilename.replace('-METADATA.XML', '-QL_QUALITY_CLASSES')),
                    baseName + '-QL_QUALITY_CLASSES.tif',
                    None
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(xmlFilename.replace('-METADATA.XML', '-QL_QUALITY_CLOUD')),
                    baseName + '-QL_QUALITY_CLOUD.tif',
                    0
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(
                        xmlFilename.replace('-METADATA.XML', '-QL_QUALITY_CLOUDSHADOW')
                    ),
                    baseName + '-QL_QUALITY_CLOUDSHADOW.tif',
                    0
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(xmlFilename.replace('-METADATA.XML', '-QL_QUALITY_HAZE')),
                    baseName + '-QL_QUALITY_HAZE.tif',
                    0
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(xmlFilename.replace('-METADATA.XML', '-QL_QUALITY_SNOW')),
                    baseName + '-QL_QUALITY_SNOW.tif',
                    0
                ),
                (
                    ImportEnmapL1BAlgorithm.findFilename(xmlFilename.replace('-METADATA.XML', '-QL_QUALITY_TESTFLAGS')),
                    baseName + '-QL_QUALITY_TESTFLAGS.tif',
                    0
                )
            ]

            for filename, outputBasename, sourceNoDataValue in subdatasets:
                parameters[alg.P_RASTER] = filename
                parameters[alg.P_OUTPUT_BASENAME] = outputBasename
                parameters[alg.P_NO_DATA_VALUE] = sourceNoDataValue
                self.runAlg(alg, parameters, None, feedback, context, True)

            result = {self.P_OUTPUT_FOLDER: folderName}
            self.toc(feedback, result)

        return result
