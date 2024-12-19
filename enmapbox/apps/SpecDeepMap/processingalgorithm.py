

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingOutputFolder,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterBoolean)
from qgis import processing

from enmapbox.apps.SpecDeepMap.core import split_raster_rois


class RasterSplitter(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    INPUT_I = 'INPUT_I'
    INPUT_L = 'INPUT_L'
    INPUT_R = 'INPUT_R'
    P_tile_x = 'tileSize_x'
    P_tile_y = 'tileSize_y'
    P_step_x = 'stepSize_x'
    P_step_y = 'stepSize_y'
    P_mode = 'Mode'
    P_OUTPUT_F: str = 'OutputFolder'
    P_removenull = 'P_removenull'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RasterSplitter()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'RasterSplitter'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('RasterSplitter')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('SpecDeepMap')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'SpecDeepMap'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Example algorithm short description")

    def shortHelpString(self):

        html = '' \
       '<p>This algorithm splits a Spectral Imaging raster and a corresponding classification label raster into smaller image tiles.Only areas, which are within or interesecting with the region of interest boundaries, are processed.</p>' \
       '<h3>Raster Image</h3>' \
       '<p>Input raster image.</p>' \
       '<h3>Raster Labels </h3>' \
       '<p>Input raster labels.</p>' \
       '<h3>Region of Interest (ROIs)</h3>' \
       '<p>Input vector defining region of interest, which is used for defining processing extents.</p>' \
       '<h3>Tile size X </h3>' \
       '<p>Tile size in X direction in Pixel Units.</p>' \
       '<h3>Tile size y </h3>' \
       '<p>Tile size in Y direction in Pixel Units.</p>' \
       '<h3>Step size X </h3>' \
       '<p>Step size in X direction in Pixel Units.</p>' \
       '<h3>Step size Y </h3>' \
       '<p>Step size in Y direction in Pixel Units.</p>' \
       '<h3>Export tiles within and interesting with ROIs </h3>' \
       '<p>This lets the user choose, to either limit the processing to tiles which lie fully in the rois or to also also include tiles which are intersecting with the rois.If this option is selected also tiles which interesct roi region are processed. For intersecting processed tiles, areas outside Roi will be set to 0. </p>' \
       '<h3>Skip tiles with no valid labels</h3>' \
       '<p>If this option is selected, the image tiles which show no valid corresponding labels will be excluded from further processing. In this system the value 0 is reserved for non valid classes. </p>' \
       '<h3>Output folder</h3>' \
       '<p>Location of output folder. In the output folder two subfolder will be created. One images and one labels. Corresponding images and labels tiles have same name.</p>'
        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_I,self.tr('Input Raster Image')))
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_L,self.tr('Input Raster Labels')))
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_R, self.tr('Regions Of Interests (ROIs)'),
            [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.P_tile_x, description='Tile size X', type=QgsProcessingParameterNumber.Integer,
            defaultValue=256, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.P_tile_y, description='Tile size Y', type=QgsProcessingParameterNumber.Integer,
            defaultValue=256, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.P_step_x, description='Step size X', type=QgsProcessingParameterNumber.Integer,
            defaultValue=256, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.P_step_y, description='Step size Y', type=QgsProcessingParameterNumber.Integer,
            defaultValue=256, minValue=1))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.P_mode, description='Export tiles intersecting and within boundaries of ROIs',
            defaultValue=False))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.P_removenull, description='Skip tiles with no valid labels',
            defaultValue=False))
        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.P_OUTPUT_F, description='Output Folder'))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        out = split_raster_rois(source_raster=self.parameterAsRasterLayer(parameters, self.INPUT_I, context).source(),
                                source_mask=self.parameterAsRasterLayer(parameters, self.INPUT_L, context).source(),
                                roi_s=self.parameterAsVectorLayer(parameters, self.INPUT_R, context).source(),
                                output_path=self.parameterAsString(parameters, self.P_OUTPUT_F, context),
                                tile_size_x=self.parameterAsInt(parameters, self.P_tile_x, context),
                                tile_size_y=self.parameterAsInt(parameters, self.P_tile_y, context),
                                x_stride=self.parameterAsInt(parameters, self.P_step_x, context),
                                y_stride=self.parameterAsInt(parameters, self.P_step_y, context),
                                mode=True,
                                remove_null=True)
        outputs = {'OutputFolder': out}
        return outputs
# 6
    def helpUrl(self, *args, **kwargs):
        return ''
# 7
    def createInstance(self):
        return type(self)()
