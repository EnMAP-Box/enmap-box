from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFolderDestination)

from enmapbox.apps.SpecDeepMap.core_raster_splitter import split_raster


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
    P_tile_x = 'tileSize_x'
    P_tile_y = 'tileSize_y'
    P_step_x = 'stepSize_x'
    P_step_y = 'stepSize_y'
    P_OUTPUT_F: str = 'OutputFolder'
    # P_removenull = 'P_removenull'
    Percent_null = 'Percent_null'
    # No_data_value = 'No_data_value'

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
        return 'Raster Splitter'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Raster Splitter')

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
               '<p>This algorithm splits a spectral imaging raster and a corresponding classification label raster into smaller image tiles(chips). Label raster must be given in Integer format.  The value zero is fixed as unclassified. Additionally, if the number of class-labels on image tiles falls below a user-specified percentage threshold, the tiles are skipped and excluded from further processing.  </p>' \
               '<h3>Raster image</h3>' \
               '<p>Input image raster in form of TIFF file. Accepts any data ranges. If No data value in raster defined, it is used to automatically set corresponindg labels in the label raster image to 0. </p>' \
               '<h3>Raster labels </h3>' \
               '<p>Input label raster in form of TIFF file. Labels are expected to be Integers in range 0-255. The value 0 is reserved for no-data class or unclassified. If label raster has zero values they will be interpreted as unclassified and masked & ignored throughout the Specdeepmap workflow. </p>' \
               '<h3>tile size X </h3>' \
               '<p>Tile size in X direction in pixel units.</p>' \
               '<h3>Tile size Y </h3>' \
               '<p>Tile size in Y direction in pixel units.</p>' \
               '<h3>Step size X </h3>' \
               '<p>Step size in X direction in pixel units.</p>' \
               '<h3>Step size Y </h3>' \
               '<p>Step size in Y direction in pixel units.</p>' \
               '<h3>Minium Class-Label Coverage per tile</h3>' \
               '<p>If the defined minimum percentage of class-labels per image tile is not reached, the tile will be skipped and excluded from further processing. The fixed label value indicating no data. or unclassified  is 0. The no data label 0 will continously be masked during training and prediction, so the model will ignore the all label pixels with the value 0. </p>' \
               '<h3>Output folder</h3>' \
               '<p>Location of output folder. In the output folder two subfolder will be created. One images and one labels. Corresponding images and labels tiles have same name.</p>'
        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_I, self.tr('Input raster image')))
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_L, self.tr('Input raster labels')))
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
        self.addParameter(QgsProcessingParameterNumber(
            name=self.Percent_null, description='Minimum Class-Label Coverage per Tile (%): ',
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=50, minValue=0, maxValue=100))

        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.P_OUTPUT_F, description='Output folder'))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        tile_counter = split_raster(raster=self.parameterAsRasterLayer(parameters, self.INPUT_I, context).source(),
                                    ds_mask=self.parameterAsRasterLayer(parameters, self.INPUT_L, context).source(),
                                    output_path=self.parameterAsString(parameters, self.P_OUTPUT_F, context),
                                    tile_size_x=self.parameterAsInt(parameters, self.P_tile_x, context),
                                    tile_size_y=self.parameterAsInt(parameters, self.P_tile_y, context),
                                    step_x=self.parameterAsInt(parameters, self.P_step_x, context),
                                    step_y=self.parameterAsInt(parameters, self.P_step_y, context),
                                    remove_null_int=self.parameterAsInt(parameters, self.Percent_null, context),
                                    feedback=feedback)
        out = self.parameterAsString(parameters, self.P_OUTPUT_F, context)
        outputs = {'OutputFolder': out}

        tiles_created = f'Total created image and label tile pairs: {tile_counter}'

        feedback.pushInfo(tiles_created)
        return outputs

    # 6
    def helpUrl(self, *args, **kwargs):
        return ''

    # 7
    def createInstance(self):
        return type(self)()
