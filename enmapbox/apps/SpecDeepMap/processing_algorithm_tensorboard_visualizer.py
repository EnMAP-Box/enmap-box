import subprocess
import time
import webbrowser

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFile)

import psutil

class Tensorboard_visualizer(QgsProcessingAlgorithm):
    """
    This is an example algorithm display.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    TENSORBOARD_LOGDIR = 'TENSORBOARD_LOGDIR'
    TENSORBOARD_PORT = 'TENSORBOARD_PORT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Tensorboard_visualizer()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'TensorBoard Visualizer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('TensorBoard Visualizer')

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
               '<p>This algorithm opens a TensorBoard (currently only for Windows system available, if used on linux, open a different port everytime you want to launch a TensorBoard). A TensorBoard is an interactive visualization tool to explore the trainings and validations metrics and losses. More details on TensorBoard you can find here: https://www.tensorflow.org/tensorboard  </p>' \
               '<h3>TensorBoard Log Directory</h3>' \
               '<p>The path which was defined during training to save model and logs.</p>' \
               '<h3>TensorBoard Port (Optional) </h3>' \
               '<p>Here you can define an additional local port to open a TensorBoard. When opening the TensorBoard it is checked if the defined port is already used for a TensorBoard, if so its closed and the new TensorBoard is launched instead </p>'
        return html

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.addParameter(
            QgsProcessingParameterFile(
                self.TENSORBOARD_LOGDIR,
                self.tr("TensorBoard Logger Directory"),
                behavior=QgsProcessingParameterFile.Behavior.Folder
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TENSORBOARD_PORT,
                self.tr("TensorBoard Port"),
                QgsProcessingParameterNumber.Integer,
                defaultValue=6006,
                optional=True
            )
        )
        self.process = None

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        logdir = self.parameterAsString(parameters, self.TENSORBOARD_LOGDIR, context)
        port = self.parameterAsInt(parameters, self.TENSORBOARD_PORT, context)

        tensorboard_command = f"tensorboard --logdir={logdir} --port={port}"

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
                    feedback.pushInfo(f"Killed process on port {port} with PID {pid}")

        else:
            feedback.pushInfo(f"No process is running on port {port}")

        # Start the TensorBoard process
        self.process = subprocess.Popen(tensorboard_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(10)

        url = f"http://localhost:{port}"
        webbrowser.open_new(url)

        # return print('Tensorboard opened at: ',port)
        feedback.pushInfo(f"TensorBoard started with PID {self.process.pid} at {logdir} on port {port}")

        process_exist = psutil.pid_exists(self.process.pid)
        process = psutil.Process(self.process.pid)
        process_runs = process.is_running()

        return {"PID": self.process.pid, "Process_exist":process_exist, "process_runs":process_runs}


    def helpUrl(self, *args, **kwargs):
        return ''

    # 7
    def createInstance(self):
        return type(self)()
