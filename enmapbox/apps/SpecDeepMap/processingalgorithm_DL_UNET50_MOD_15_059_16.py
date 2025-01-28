from qgis._core import QgsProcessingParameterDefinition

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingOutputFolder,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterVectorLayer)
from qgis import processing
import random
import subprocess
import time
import webbrowser

from enmapbox.apps.SpecDeepMap.core_DL_UNET50_MOD_15_059_16 import dl_train

class DL_Train_MOD(QgsProcessingAlgorithm):
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


    # In einer zeile
    #train_data_csv = 'train_data_csv'
    #val_data_csv = 'val_data_csv'
    train_val_input_folder ='input_folder'
    arch = 'arch'
    backbone= 'Backbone'
    pretrained_weights = 'pretrained_weights'
    freeze_encoder = 'freeze_encoder'
    data_aug = 'data_aug'
    batch_size = 'Batchsize'
    n_epochs = 'Epochs'
    lr ='learning rate'
    lr_finder = 'lr_finder'
    pat= 'patience'
    ignore_index= 'ignore index'
    class_weights_balanced = ' class_weights_balanced'
    normalization_flag = 'normalization'
    num_workers = 'Number of workers'
    device = 'Device'
    device_numbers ='Device Numbers'
    logdirpath = 'logdirpath '
    checkpoint = 'checkpoint'
    n_classes = 'n_classes'
    tensorboard = 'tensorboard'
    num_models = 'num_models'
    logdirpath_model = 'logdirpath_model'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DL_Train()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Deep Learning Trainer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Deep Learning Trainer')

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
       '<p>This algorithm trains a deep learning model specifically a Unet, Unet++ or DeeplabV3+ model with a definable backbone for a semantic segmentation task. For Training the model a Cross-entropy loss or balanced Cross-entropy loss is used. The performance metric, which is used for training is Intersection over Union.</p>' \
       '<h3>Training dataset</h3>' \
       '<p>Input is a CSV-file of the trainings dataset.</p>' \
       '<h3>Validation dataset</h3>' \
       '<p>Input is a CSV-file of the validation dataset.</p>' \
       '<h3>Deep learning model: architecture</h3>' \
       '<p>The main architecture for the deep learning model can be defined with this variable. Options are Unet, Unet++ and DeeplabV3+.</p>' \
       '<h3>Deep learning model: backbone</h3>' \
       '<p> The model can be built with several backbones from pytorch segmentation models libary, e.g. ResNet 50, ResNeXt, EfficientNet. For more options look into pytorch segmentation models libary here https://github.com/qubvel/segmentation_models.pytorch .</p>' \
       '<h3>Load pretrained weights </h3>' \
       '<p>Here a user can chose weights for model initalization, imagenet weight are default and compatibel will all backbones. More different weight for ResNet50 will be provided e.g. Sentinel-2 </p>' \
       '<h3>Load model from path</h3>' \
       '<p>Load model from path for continuing training or to initalize a model. Restriction is that model must be compatibel with training scheme and input data type. </p>' \
       '<h3>Freeze backbone </h3>' \
       '<p>This freezes the weight of the backbone for training. This is a routine step for transferlearning where in the first step a model is trained on new classes with a frozen backbone and in a second training step it is finetuned with an unfrozen backbone. To achieve this here, train first with frozen backbone and then load trained model again and train with unfrozen backbone. </p>' \
       '<h3>Data augmentation (random flip & rotate by 45°) </h3>' \
       '<p>This apply data augmentation. Random vertical and horizontal flip as well as ranodm rotate with 45°. Each augmentation has a propability of occuring of 50 %. This data augmentation is happening on the fly and prevents overfitting of the model. </p>' \
       '<h3>Early stopping</h3>' \
       '<p>This stops the model when validation loss is not imporving for 50 epochs.  </p>' \
       '<h3>Batch size</h3>' \
       '<p>This defines the number of images which are porcessed in batches. </p>' \
       '<h3>Epochs</h3>' \
       '<p>This defines the number of Epochs which are used to train a model. One epochs means the model is trained once on the whole training dataset. </p>' \
       '<h3>Learning rate</h3>' \
       '<p>This defines the Learning rate for the Adam optimizer of the model. </p>' \
       '<h3>Ignore Index</h3>' \
       '<p>Via this index you can exclude a class e.g. background from the Intersection over Union calculation. This has just influence on the Metric calculation. If you have a class imbalance use class weights.</p>' \
       '<h3>Class weights</h3>' \
       '<p> If you have a class imbalance use class weights.This load precomputed class weights from the dataset summary CSV.</p>' \
       '<h3>Number of workers</h3>' \
       '<p>This defines number of cpus used for data loading and augmentation and supports your training speed.</p>' \
       '<h3>Type of device</h3>' \
       '<p> You can use either CPU or GPU for training. If available use GPU.</p>' \
       '<h3>Number of devices</h3>' \
       '<p> For distributated training you can also here define how many GPUs you want to use. </p>' \
       '<h3>Path for saving model and Tensorboard logger</h3>' \
       '<p>Define folder where models are saved and Tensorboard logger is saved. </p>'

        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        #     class_weights = 'class weights'
        #     num_workers = 'Number of workers'
        #     device = 'Device'
        #     device_numbers ='Device Numbers'
        #     logdirpath = 'Model and Logger path'
        #
        #self.addParameter(
         #   QgsProcessingParameterVectorLayer(self.train_data_csv,self.tr('Trainings dataset')))
        #self.addParameter(
         #   QgsProcessingParameterVectorLayer(self.val_data_csv, self.tr('Validation dataset')))
        self.addParameter(QgsProcessingParameterFile(
            name=self.train_val_input_folder, description='Input folder (Train and Validation dataset)',behavior=QgsProcessingParameterFile.Behavior.Folder))


        #self.addParameter(QgsProcessingParameterFile(
         #   name=self.train_data_csv, description='Train dataset', behavior=QgsProcessingParameterFile.Behavior.File))
        #self.addParameter(QgsProcessingParameterFile(
         #   name=self.val_data_csv, description='Val dataset', behavior=QgsProcessingParameterFile.Behavior.File))
        #self.addParameter(QgsProcessingParameterString(
         #   name=self.arch, description='Model architecture', defaultValue='Unet'))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.arch, description='Model architecture', options=['Unet', 'Unet++','DeepLabV3+','MAnet','JustoUNetSimple'], defaultValue=0))
        self.addParameter(QgsProcessingParameterString(
            name=self.backbone, description='Model backbone',defaultValue='resnet18'))
        self.addParameter(QgsProcessingParameterEnum(
            name=self.pretrained_weights, description='Load pretrained weights',
            options=['imagenet', 'None', 'Sentinel_2_TOA_Resnet18','Sentinel_2_TOA_Resnet50'], defaultValue=0))
        #options = ['imagenet', 'None', 'Sentinel_2_TOA_Resnet18', 'Sentinel_2_TOA_Resnet50', 'LANDSAT_TM_TOA_Resnet18',
         #          'LANDSAT_ETM_TOA_Resnet18', 'LANDSAT_OLI_TIRS_TOA_Resnet18', 'LANDSAT_ETM_SR_Resnet18',
          #         'LANDSAT_OLI_SR_Resnet18'], defaultValue = 0))

        #self.addParameter(QgsProcessingParameterString(
         #   name=self.pretrained_weights, description='Load pretrained weights',defaultValue='imagenet'))
        #self.addParameter(QgsProcessingParameterNumber(
         #   name=self.n_classes, description='Number of classes', type=QgsProcessingParameterNumber.Integer,
          #  defaultValue=20))

        self.addParameter(QgsProcessingParameterFile(self.checkpoint, description='Load model from path', optional=True))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.freeze_encoder, description='Freeze backbone',
            defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.data_aug, description='Data augmentation (random flip & rotate by 45°)',
            defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.pat, description='Early stopping',
            defaultValue=True))
        self.addParameter(
            QgsProcessingParameterBoolean(self.class_weights_balanced, self.tr('Balanced Training using Class Weights'),defaultValue=True))
        self.addParameter(
            QgsProcessingParameterBoolean(self.normalization_flag, self.tr('Data Normalization'), defaultValue=False))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.tensorboard, description='Open Tensorboard after training',
            defaultValue=True))


        self.addParameter(QgsProcessingParameterNumber(
            name=self.batch_size , description='Batch size', type=QgsProcessingParameterNumber.Integer,
            defaultValue=2, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.n_epochs, description='Epochs', type=QgsProcessingParameterNumber.Integer,
            defaultValue=1, minValue=1))

        self.addParameter(QgsProcessingParameterNumber(
            name=self.lr, description='Learning rate', type=QgsProcessingParameterNumber.Double,
            defaultValue=0.001, minValue=0.0000001))
        self.addParameter(QgsProcessingParameterBoolean(
            name=self.lr_finder, description='Automatic learning rate finder',
            defaultValue=False))

        self.addParameter(QgsProcessingParameterEnum(
            name=self.device, description='Type of device (GPU/CPU)', options=['cpu', 'gpu'], defaultValue=0))

        ### adjusted   to make advanced

        p = QgsProcessingParameterNumber(
            name=self.num_workers , description='Number of workers (CPUs used for data loading and augumenation)', type=QgsProcessingParameterNumber.Integer,
            defaultValue=0)
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(p)

        p1 = QgsProcessingParameterNumber(
            name=self.device_numbers, description='Number of devices (GPU/CPU)',optional=True,
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=1, minValue=0)
        p1.setFlags(p1.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(p1)

        p2 = QgsProcessingParameterNumber(
            name=self.num_models, description='Number of Models', optional=True,
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=1)
        p2.setFlags(p2.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(p2)

        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.logdirpath, description='Path for saving Tensorboard logger'))

        self.addParameter(QgsProcessingParameterFolderDestination(
            name=self.logdirpath_model, description='Path for saving model'))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        dl_train(#train_data_csv = self.parameterAsVectorLayer(parameters, self.train_data_csv, context),
                       #val_data_csv= self.parameterAsVectorLayer(parameters, self.val_data_csv, context),
                       #train_data_csv=self.parameterAsString(parameters, self.train_data_csv, context),
                       #val_data_csv = self.parameterAsString(parameters, self.val_data_csv, context),
                       input_folder=  self.parameterAsString(parameters, self.train_val_input_folder,context),
                       #arch=self.parameterAsString(parameters, self.arch, context),
                       arch_index=self.parameterAsEnum(parameters, self.arch, context),
                       backbone = self.parameterAsString(parameters, self.backbone, context),
                       #pretrained_weights = self.parameterAsString(parameters, self.pretrained_weights, context),
                       pretrained_weights_index=self.parameterAsEnum(parameters, self.pretrained_weights, context),
                       #n_classes = self.parameterAsInt(parameters, self.n_classes, context),
                       checkpoint_path = self.parameterAsFile(parameters,self.checkpoint, context),
                       freeze_encoder=self.parameterAsBool(parameters, self.freeze_encoder, context),
                       data_aug=self.parameterAsBool(parameters, self.data_aug, context),
                       batch_size=self.parameterAsInt(parameters, self.batch_size, context),
                       n_epochs=self.parameterAsInt(parameters, self.n_epochs, context),
                       lr=self.parameterAsDouble(parameters, self.lr, context),
                       tune=self.parameterAsBool(parameters, self.lr_finder, context),
                       early_stop=self.parameterAsBool(parameters, self.pat, context),
                       #ignore_index =self.parameterAsInt(parameters, self.ignore_index, context),
                       class_weights_balanced=self.parameterAsBool(parameters, self.class_weights_balanced, context),
                       normalization_bool= self.parameterAsBool(parameters, self.normalization_flag, context),
                       num_workers=self.parameterAsInt(parameters, self.num_workers, context),
                       #acc_type=self.parameterAsString(parameters, self.device, context),
                       num_models =self.parameterAsInt(parameters, self.num_models, context),
                       acc_type_index=self.parameterAsEnum(parameters, self.device, context),
                       acc_type_numbers=self.parameterAsInt(parameters, self.device_numbers, context),
                       logdirpath=self.parameterAsString(parameters, self.logdirpath, context),
                       logdirpath_model =self.parameterAsString(parameters, self.logdirpath_model, context),
                       feedback =feedback)

        feedback.pushInfo("Training completed.")

        out = self.parameterAsString(parameters, self.logdirpath, context)

        tensorboard_open = self.parameterAsBool(parameters, self.tensorboard, context)


        if tensorboard_open  == True:

            port = 6006

            tensorboard_command = f"tensorboard --logdir={out} --port={port}"

            # Use netstat to find any process using the specified port and get the PID
            cmd_find_pid = f"netstat -aon | findstr :{port}"
            result = subprocess.run(cmd_find_pid, shell=True, capture_output=True, text=True)

            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) > 4 and parts[1].endswith(f":{port}"):
                        pid = parts[4]  # PID is the fifth element
                        # Kill the process using the PID
                        cmd_kill = f"taskkill /PID {pid} /F"
                        subprocess.run(cmd_kill, shell=True)
                        feedback.pushInfo(f"Killed process on port {port} with PID {pid}, and initalizied Tensorboard on same port")
            else:
                feedback.pushInfo(f"No process is running on port {port},initalizied Tensorboard on same port")

            # Start the TensorBoard process
            self.process = subprocess.Popen(tensorboard_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            time.sleep(10)
            url = f"http://localhost:{port}"
            webbrowser.open_new(url)


        outputs = {self.logdirpath: out}
        return outputs
# 6
    def helpUrl(self, *args, **kwargs):
        return ''
# 7
    def createInstance(self):
        return type(self)()

