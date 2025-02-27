from qgis.PyQt.QtCore import QCoreApplication
from qgis._core import QgsProcessingParameterEnum
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination)

from enmapbox.apps.SpecDeepMap.core_deep_learning_mapper import pred_mapper


class DL_Mapper(QgsProcessingAlgorithm):
    """DL_Train
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

    P_input_raster = 'input_raster'
    # In einer zeile
    # P_out_put = 'out_put'
    P_model_checkpoint = 'model_checkpoint'
    # P_tile_size_x = 'tile_size_x'
    # P_tile_size_y = 'tile_size_y'
    P_overlap = 'overlap'
    P_gt_path = 'gt_path'
    #P_ignore_index = 'ignore_index'
    P_vector = 'vector'
    # P_no_data_value = 'no_data_value'
    P_acc = 'acc'
    P_raster_output = 'raster_output'
    P_vector_output = 'vector_output'
    P_csv_output = 'csv_output'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DL_Mapper()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Deep Learning Mapper'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Deep Learning Mapper')

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
               '<p>This algorithm loads a trained deep learning model and uses it for prediction. The algorithm can load complete satelite szences and splits it on the fly in small tiles predicts on them and stich them back together. The prediction is saves as a raster and can also be saved as a vector layer. If a ground truth mask is given the performance metric,Intersection over Union is calculated per class and a general mean.</p>' \
               '<h3>Input Raster</h3>' \
               '<p>Input spectral raster, which should be predicted</p>' \
               '<h3>Ground truth raster (Optional)</h3>' \
               '<p>Ground truth label raster, which can be used to asses the model performances. If this is given an Intersection Union metric per class as well as a mean is calculated.</p>' \
               '<h3>Model checkpoint</h3>' \
               '<p>The file path from which to load the trained model.</p>' \
               '<h3>Minimum overlap of tiles in Pixel Unit</h3>' \
               '<p>As this algorithm loads the input raster in small tiles, an can be defined with this parameter. This overlap is cropped from each predicted tile in directions to other tiles, so that there is no actual overlap in the prediction, but boundary effect are minimized. A good suggestion is 5-10% of image size. If the overlap doesnt lead to full coverage, the overlap is adjusted to next possible solution, to give full coverage of prediction </p>' \
               '<h3>Ignore Index (Optional)</h3>' \
               '<p>This exculdes the specified class from the individual class metrics and from the mean IoU calculation</p>' \
               '<h3>Export prediction as VectorLayer</h3>' \
               '<p>If this is checked than the predcition will also be saved as Vector Layer in the output folder. </p>' \
               '<h3>Device</h3>' \
               '<p>Define if you use CPU or GPU for the prediction</p>' \
               '<h3>Output folder</h3>' \
               '<p>The prediction will be saved in this folder as raster and as shapefile, if wanted. Further a the individual class Intersection over Unionin scores as well as a mean (IoU) are saved as a csv file.  </p>'
        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.P_input_raster, self.tr('Input Raster')))

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.P_gt_path, 'Ground Truth Raster'))

        self.addParameter(QgsProcessingParameterFile(
            name=self.P_model_checkpoint, description='Model Checkpoint',
            behavior=QgsProcessingParameterFile.Behavior.File))

        self.addParameter(QgsProcessingParameterNumber(
            name=self.P_overlap, description='Minimum overlap of tiles in Percentage',
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=10))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_acc, description='Device', options=['cpu', 'gpu'], defaultValue=0))


        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.P_raster_output,
                'Predicition as Raster',
                optional=False
            )
        )
        # Optional vector output
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.P_vector_output,
                'Prediction as Vector Output',
                optional=True, createByDefault=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.P_csv_output,
                'IoU CSV (needs Ground Truth Raster Input))',
                fileFilter='CSV files (*.csv)',
                optional=True, createByDefault=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # feedback.setProgress(42)
        # feedback.pushInfo('Hello World')

        pred_mapper(input_raster=self.parameterAsRasterLayer(parameters, self.P_input_raster, context).source(),
                    model_checkpoint=self.parameterAsFile(parameters, self.P_model_checkpoint, context),
                    overlap=self.parameterAsInt(parameters, self.P_overlap, context),
                    gt_path=self.parameterAsRasterLayer(parameters, self.P_gt_path, context).source(),
                    acc=self.parameterAsEnum(parameters, self.P_acc, context),
                    feedback=feedback,
                    raster_output=self.parameterAsOutputLayer(parameters, self.P_raster_output, context),
                    vector_output=self.parameterAsOutputLayer(parameters, self.P_vector_output, context),
                    csv_output=self.parameterAsFileOutput(parameters, self.P_csv_output, context)
                    )
        raster_output = self.parameterAsOutputLayer(parameters, self.P_raster_output, context)
        vector_output = self.parameterAsOutputLayer(parameters, self.P_vector_output, context)
        csv_output = self.parameterAsFileOutput(parameters, self.P_csv_output, context)

        outputs = {self.P_raster_output: raster_output, self.P_vector_output: vector_output,
                   self.P_csv_output: csv_output}

        return outputs

    # 6
    def helpUrl(self, *args, **kwargs):
        return ''

    # 7
    def createInstance(self):
        return type(self)()
