from os.path import join, dirname
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing

import psutil
from enmapbox.apps.SpecDeepMap.processing_algorithm_tensorboard_visualizer import Tensorboard_visualizer
import webbrowser
from enmapbox import exampledata
import subprocess
import time
import glob
from enmapboxprocessing.testcase import TestCase

class Test_Tensorboard(TestCase):

    def test_init(self):

      # init QGIS
      qgsApp = QgsApplication([], True)
      qgsApp.initQgis()
      qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

      # init processing framework
      Processing.initialize()

      # run algorithm
      alg = Tensorboard_visualizer()

      # Define paths
      BASE_DIR = dirname(__file__)
      folder_path_logs = join(BASE_DIR, "test_run/")


      io = {alg.TENSORBOARD_LOGDIR: folder_path_logs,
            alg.TENSORBOARD_PORT: 6006}

      result = Processing.runAlgorithm(alg, parameters=io)

      print(result)

      # Get the process with the given PID
      process = psutil.Process(result['PID'])

      # Assert if the process is running
      assert process.is_running(), f"Process with PID {result['PID']} is not running."

      # Clean up

      # Kill the process after the check

      #time.sleep(15)   process kills also tensorboard directly after creating. if check if tensorbard gui is open unhashtag this line

      process = psutil.Process(result['PID'])
      # Recursively kill all child processes
      for child in process.children(recursive=True):
        child.kill()  # Force kill child processes

      # Kill the main process
      process.kill()


