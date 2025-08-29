from qgis.PyQt.QtCore import QCoreApplication
from qgis._core import QgsProcessingParameterEnum
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFileDestination)


class DL_Tester(QgsProcessingAlgorithm):
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

    P_test_data_csv = 'test_data_csv'
    P_model_checkpoint = 'model_checkpoint'
    P_acc_device = 'acc_device'
    P_csv_output_tester = 'csv_output_tester'
    P_folder_preds = 'folder_preds'
    P_no_data_label_mask = 'no_data_label_mask'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DL_Tester()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Deep Learning Tester'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Deep Learning Tester')

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
               '<p>This algorithm loads a trained deep learning model and uses it for prediction on the test dataset. The Intersection over Union (IoU) score per class as well as overall mean is saved as csv-file. Optionally all predicted chips can be exported and saved as tiff files.</p>' \
               '<h3>Test dataset</h3>' \
               '<p>Load the test_files.csv created by the Dataset Maker</p>' \
               '<h3>Model Checkpoint</h3>' \
               '<p>Load the model checkpoint file of saved model during training (choose the one with highest IoU on val dataset - is written in checkpoint name) </p>' \
               '<h3>Device </h3>' \
               '<p>Can be run on CPU or GPU, if GPU available and correctly installed</p>' \
               '<h3>Crop unclassified-labels from prediction</h3>' \
               '<p>If this is true, unclassified values indicated by 0 are cropped from prediction before the image chips are exported. Unclassified labels with value 0 are always ignore in score calculation. So this is just relevant if you want to export tiles intersecting image boundaries or have sparse labels.  </p>' \
               '<h3>IoU CSV</h3>' \
               '<p>Location where IoU score csv-file will be created</p>' \
               '<h3>Save and export prediction image to folder (optional)</h3>' \
               '<p>If a folder location is specified all prediction images will be saved in given folder</p>'
        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(QgsProcessingParameterFile(
            name=self.P_test_data_csv, description='Test dataset', behavior=QgsProcessingParameterFile.Behavior.File))

        self.addParameter(QgsProcessingParameterFile(
            name=self.P_model_checkpoint, description='Model Checkpoint',
            behavior=QgsProcessingParameterFile.Behavior.File))

        self.addParameter(QgsProcessingParameterEnum(
            name=self.P_acc_device, description='Device', options=['cpu', 'gpu'], defaultValue=0))

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.P_csv_output_tester,
                'IoU CSV',
                fileFilter='CSV files (*.csv)'

            )
        )
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.P_no_data_label_mask, description='Crop unclassified-labels from prediction',
            defaultValue=True))

        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.P_folder_preds, description='Save and export prediction images to folder', optional=True,
            createByDefault=False))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        from enmapbox.apps.SpecDeepMap.core_tester import process_images_from_csv

        process_images_from_csv(csv_file=self.parameterAsFile(parameters, self.P_test_data_csv, context),
                                model_checkpoint=self.parameterAsFile(parameters, self.P_model_checkpoint, context),
                                acc_device=self.parameterAsEnum(parameters, self.P_acc_device, context),
                                csv_output_path=self.parameterAsFileOutput(parameters, self.P_csv_output_tester,
                                                                           context),
                                export_folder=self.parameterAsFileOutput(parameters, self.P_folder_preds, context),
                                no_data_label_mask=self.parameterAsBool(parameters, self.P_no_data_label_mask, context),
                                feedback=feedback,
                                )

        csv_output_path = self.parameterAsFileOutput(parameters, self.P_csv_output_tester, context),
        export_folder = self.parameterAsFileOutput(parameters, self.P_folder_preds, context),

        outputs = {self.P_csv_output_tester: csv_output_path, self.P_folder_preds: export_folder}

        return outputs

    # 6
    def helpUrl(self, *args, **kwargs):
        return ''

    # 7
    def createInstance(self):
        return type(self)()
