
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
               '<p>This algorithm launches TensorBoard, an interactive visualization tool for exploring training and validation metrics and losses. More details on TensorBoard you can find here: https://www.tensorflow.org/tensorboard . Once started, TensorBoard runs in the background on your local host until QGIS is closed. Running TensorBoard will not affect the performance of other algorithms. If the chosen port is already in use, please select a different one.</p>' \
               '<h3>TensorBoard Log Directory</h3>' \
               '<p> Select the folder that was defined during training to save TensorBoard logs.This directory usually contains a lightning_logs subfolder.However, the algorithm also works if you provide the main training output folder where the logs are stored. </p>'\
               '<h3>TensorBoard Port (Optional) </h3>' \
               '<p> You can specify a local port number for launching a TensorBoard.If the chosen port is already in use, please select another port within the range 6006–65535. A new TensorBoard instance will then be started on that port.All TensorBoard ports are automatically released/closed when QGIS is closed.< / p >'
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

    def processAlgorithm(self, parameters, context, feedback):

        from qgis.PyQt.QtCore import QTimer
        from tensorboard import program
        import webbrowser


        logdir = self.parameterAsString(parameters, self.TENSORBOARD_LOGDIR, context)
        port = self.parameterAsInt(parameters, self.TENSORBOARD_PORT, context)

        tb_run = False

            # Start TensorBoard
        tb = program.TensorBoard()
        tb.configure(argv=[
                None,
                "--logdir", logdir,
                "--port", str(port),
                "--host", "127.0.0.1",
            ])
        url = tb.launch()

        if url:
            tb_run = True

        feedback.pushInfo(f"TensorBoard running in background at {url}. If not directly opened you can open TensorBoard by copying: {url} in your browser.")
        feedback.pushInfo(f"TensorBoard will run in background until QGIS is closed, but will not interfere with other algorithms performances and can be ignored.")
        feedback.pushInfo(f"If you want to initalize a different TensorBoard, just change the port number and run the algorithm again.")
        webbrowser.open_new(url)

            # Timer to check cancel periodically




        return {"TensorBoard_run": tb_run}

    def helpUrl(self, *args, **kwargs):
        return ''

    # 7
    def createInstance(self):
        return type(self)()