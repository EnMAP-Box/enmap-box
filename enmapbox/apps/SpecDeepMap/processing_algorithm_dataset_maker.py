from qgis.PyQt.QtCore import QCoreApplication
from qgis._core import QgsProcessingParameterDefinition
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
    # QgsProcessingParameterFolder,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterBoolean)

from enmapbox.apps.SpecDeepMap.core_dataset_maker import create_train_validation_csv_balance


class DatasetMaker(QgsProcessingAlgorithm):
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
    # D_split = 'Default_Split'
    N_train = "Train images"
    N_test = 'Test images'
    N_val = 'Validation images'
    # N_train = "Train images"
    Seed = 'Random Seed'
    Shuffle = 'Shuffle'
    # Data_type = 'Datatypedefault:tif'
    Output_path = 'Outputfolderpath'
    scaler = "Scaler"
    normalize = "normalize"
    # N_classes = 'Number of classes'
    N_permute = "permute"

    # P_OUTPUT_F: str = 'OutputFolder'
    # P_removenull = 'P_removenull'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DatasetMaker()

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
               '<p>This algorithm creates training, validation and test datasets in CSV format. Each created dataset consists of images and their corresponding labels. The data can be split by default in 80% training, 10 % validation dataset, 10 % test dataset. The algorithm aims to achieve an equal class distribution with a deviation of 1 % per class per dataset, for this a wasserstein distance and the permutatation is used. The algorith further generates a summary of class counts per dataset as well as there percentage and to calculate class weights.Additionaly the algorithm can calculate mean and standard deviation,per channel in the train dataset which can be used for data normalization during training.</p>' \
               '<h3>Data folder</h3>' \
               '<p>Folder which contains an image chip folder and corresponding label chip folder.</p>' \
               '<h3>Percentage of train images</h3>' \
               '<p>Defines how much percentage of the data is used as train dataset. </p>' \
               '<h3>Percentage of validation images</h3>' \
               '<p>Defines how much percentage of the data is used as validation dataset.</p>' \
               '<h3>Percentage of test images</h3>' \
               '<p>Defines how much percentage of the data is used as test dataset.</p>' \
               '<h3>Scaler</h3>' \
               '<p>Optional parameter, if a scaler is defined, the scaler is used during training and prediction to scale image data between values of 0-1. </p>' \
               '</p>To scale data in a range of 0-1, the scaler should be the maximum possible value of the image data.</p>' \
               '<p>If use of pretrained imagenet weight is intended, the data must be scaled to a range 0-1 to be compatibale with the pretrained weights. </p>' \
               '<h3>Create Normalisation Statistic ( Mean and std. per Channel)</h3>' \
               '<p>If this parameter is activated, it creates a normalisation statistic in form of a csv file. Listing the mean and std. per Channel for the training dataset. </p>' \
               '<p>If a scaler was defined it is also taken into account to scale mean and std. accordingly. This normalization statistic can be used to normalize the data during training and prediction. If pretrained Imagenet weights are intended to be used, for more then 3 channels, a computation of normalisation statistic is requiered. </p>' \
               '<h3>Number of permutation of Wasserstein distance </h3>' \
               '<p>This parameter defiend how many permutations the Wasserstein distance can use to find an similar datasplit. If any class in the data is not reaching the min value of 0.001 per dataset the algorithm yields an error. As it only make sense to include data which is actually present in the dataset, the algorithm doesnt allow inclusion of barley existing classes. Id this is happening you should think about your classification structure and restructure your input data.</p>' \
               '<h3>Random seed </h3>' \
               '<p>Seed ensures that the same random starting point can be used for the data split calculations. </p>' \
               '<h3>Output folder</h3>' \
               '<p>Location of output folder. In the output folder the csv-files are generated.  there is one csv file generated for training, validation and test dataset as well as one summary csv and optionally also a normalization csv.</p>'
        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.

        self.addParameter(QgsProcessingParameterFile(
            name=self.Train_Val_folder, description='Data folder', behavior=QgsProcessingParameterFile.Behavior.Folder))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_train, description='Percentage of train images',
            defaultValue=80))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_test, description='Percentage of test images',
            defaultValue=10))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_val, description='Percentage of validation images',
            defaultValue=10))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.scaler, description='Scaler', type=QgsProcessingParameterNumber.Integer,
            defaultValue=None, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.normalize, description='Create Normalization Statistic (Mean and Std. per Channel)',
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

        # self.addParameter(QgsProcessingParameterVectorDestination(name=self.df_val, description='Data type default : tif'))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        b = create_train_validation_csv_balance(
            input_folder=self.parameterAsString(parameters, self.Train_Val_folder, context),
            out_folder_path=self.parameterAsString(parameters, self.Output_path, context),
            train_int_perc=self.parameterAsInt(parameters, self.N_train, context),
            test_int_perc=self.parameterAsInt(parameters, self.N_test, context),
            val_int_perc=self.parameterAsInt(parameters, self.N_val, context),
            random_seed_gen=self.parameterAsInt(parameters, self.Seed, context),
            normalize=self.parameterAsBool(parameters, self.normalize, context),
            feedback=feedback,
            scaler=self.parameterAsInt(parameters, self.scaler, context),
            min_perc=0.01,
            num_permutations=self.parameterAsInt(parameters, self.N_permute, context))

        output_folder = self.parameterAsString(parameters, self.Output_path, context)
        outputs = {'Output': output_folder}
        # outputs = b

        feedback.pushInfo(b)

        return outputs

    # 6
    def helpUrl(self, *args, **kwargs):
        return ''

    # 7
    def createInstance(self):
        return type(self)()
