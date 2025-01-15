
from qgis._core import QgsProcessingParameterDefinition

from qgis.PyQt.QtCore import QCoreApplication
from qgis._core import QgsProcessingParameterVectorDestination
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingOutputFolder,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       #QgsProcessingParameterFolder,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString)
from qgis import processing


from enmapbox.apps.SpecDeepMap.core_DS_SUM12 import create_train_validation_csv_balance

class DatasetSplitter_SUM(QgsProcessingAlgorithm):
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

    Train_Val_folder = 'Train_Val_Folder'
    #D_split = 'Default_Split'
    N_train = "Train images"
    N_test = 'Test images'
    N_val = 'Validation images'
    #N_train = "Train images"
    Seed = 'Random Seed'
    Shuffle = 'Shuffle'
    Data_type = 'Datatypedefault:tif'
    Output_path = 'Outputfolderpath'
    scaler ="Scaler"
    normalize ="normalize"
    #N_classes = 'Number of classes'
    N_permute ="permute"


    #P_OUTPUT_F: str = 'OutputFolder'
    #P_removenull = 'P_removenull'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DatasetSplitter_SUM()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Dataset Maker'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Dataset Maker')

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
       '<p>This algorithm creates training, validation and test datasets in CSV format. Each created dataset consists of images and their corresponding labels. The data can be split by default in 80% training, 10 % validation dataset, 10 % test dataset. The test and valdiation dataset are defined by percantage and the remaining percent will be in the training dataset. it is aimed to achieve an equal class distribution with a deviation of 1 % per class per dataset, for this a wasserstein distance and the permute is used. The algorith further generates a summariy of class counts perdataset as well as there percentage and to calculate class weights.Additionaly the algorith can calculate mean and std,per channel in the train dataset whcih can be used for data normalization during training.</p>' \
       '<h3>Data folder</h3>' \
       '<p>Folder location which contains an image tile and corresponding label tile folder.</p>' \
       '<h3>Default split </h3>' \
       '<p>Data is split in 80% training and 20 % validation dataset. </p>' \
       '<h3>Percent training images</h3>'\
       '<p>User definable percentage  of images, which should be in training dataset. If "%" is used after number it is interpreted as percent, else as actual number. Default is "80%" training images, including automatic rounding.</p>' \
       '<h3>Percent or number of validation images</h3>' \
       '<p>User definable percentage or actul number of images, which should be in validation dataset. If "%" is used after number it is interpreted as percent, else as actual number. Default is "20%"  validation images, including automatic rounding.</p>' \
       '<h3>Random seed </h3>' \
       '<p>Defines seed for random split. Seed number is needed to generated again same random split if necessary. </p>' \
       '<h3>Shuffle </h3>' \
       '<p>Shuffled the data randomly before split.</p>' \
       '<h3>Data type </h3>' \
       '<p>Defines which data type for images and labels should be considered.</p>' \
       '<h3>Create training and valdiation dataset summary and class weights</h3>' \
       '<p>This generates a summary CSV , which gives an overview of how many pixel per class are in the training dataset and validation dataset. And further generates class weights for a balanced training on the base of the class distribution of the training dataset. </p>' \
       '<h3>Output folder</h3>' \
       '<p>Location of output folder. In the output folder the csv-files are generated.</p>'
        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.

        self.addParameter(QgsProcessingParameterFile(
            name=self.Train_Val_folder, description='Data folder',behavior=QgsProcessingParameterFile.Behavior.Folder))
        #self.addParameter(QgsProcessingParameterBoolean(
         #   name=self.D_split, description='Default split',
          #  defaultValue=True))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_train, description='Percentage of train images',
            defaultValue=80))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_test, description='Percentage of test images',
            defaultValue=10))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_val, description='Percentage of validation images',
            defaultValue=10))
        #self.addParameter(QgsProcessingParameterNumber(
         #   name=self.N_classes, description='Number of Classes',
          #  defaultValue=19))



        #self.addParameter(
        #self.addParameter(QgsProcessingParameterString(
         #   name=self.Data_type, description='Data type',  defaultValue="tif"))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.Data_type, description='Data type', options=['tif', 'jpg','jpeg','png'], defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.scaler, description='Scaler', type=QgsProcessingParameterNumber.Integer,
            defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.normalize , description='Create Normalization Statistic (Mean and Std. per Channel)',
            defaultValue=True))
        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.Output_path, description='Output folder'))

        p = QgsProcessingParameterNumber(
            name=self.N_permute, description='Number of permutation for Wassestein distance',
            defaultValue=100000)
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(p)

        p1 = QgsProcessingParameterNumber(
            name=self.Seed, description='Random seed', type=QgsProcessingParameterNumber.Integer,
            defaultValue=42, minValue=0)
        p1.setFlags(p1.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(p1)
        #self.addParameter(QgsProcessingParameterVectorDestination(name=self.df_val, description='Data type default : tif'))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """


        b  = create_train_validation_csv_balance(input_folder=self.parameterAsString(parameters, self.Train_Val_folder,context),
                                                     out_folder_path=self.parameterAsString(parameters, self.Output_path, context),
                                                     train_int_perc=self.parameterAsInt(parameters, self.N_train, context),
                                                     test_int_perc=self.parameterAsInt(parameters, self.N_test, context),
                                                     val_int_perc=self.parameterAsInt(parameters, self.N_val, context),
                                                     #num_labels=None,
                                                     random_seed = self.parameterAsInt(parameters, self.Seed, context),
                                                     datatyp_index = self.parameterAsEnum(parameters, self.Data_type, context),
                                                     normalize = self.parameterAsBool(parameters, self.normalize , context),
                                                     feedback =feedback,
                                                     scaler = self.parameterAsInt(parameters, self.scaler, context),
                                                     min_perc=0.01,
                                                     num_permutations =self.parameterAsInt(parameters, self.N_permute, context))
        # dictanory . train, val, test.

        output_folder = self.parameterAsString(parameters, self.Output_path, context)
        outputs = {'Output': output_folder}
        #outputs = b

        feedback.pushInfo(b)

        return outputs
# 6
    def helpUrl(self, *args, **kwargs):
        return ''
# 7
    def createInstance(self):
        return type(self)()
