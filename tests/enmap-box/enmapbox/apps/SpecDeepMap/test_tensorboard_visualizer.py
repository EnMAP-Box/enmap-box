import os
import shutil
from pathlib import Path

import psutil
from processing.core.Processing import Processing

from enmapbox import DIR_UNITTESTS
from enmapbox.apps.SpecDeepMap.processing_algorithm_tensorboard_visualizer import Tensorboard_visualizer
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase

start_app()


class Test_Tensorboard(TestCase):

    def test_init(self):

        # init QGIS
        # qgsApp = QgsApplication([], True)
        # qgsApp.initQgis()
        # qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

        # init processing framework
        Processing.initialize()

        # run algorithm
        alg = Tensorboard_visualizer()

        # Define paths
        BASE_DIR = Path(__file__).parent
        BASE_TESTDATA = Path(DIR_UNITTESTS) / 'testdata/external/specdeepmap'
        folder_path_logs = BASE_TESTDATA / "test_requierments"

        io = {alg.TENSORBOARD_LOGDIR: str(folder_path_logs),
              alg.TENSORBOARD_PORT: 6006}

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # Get the process with the given PID
        process = psutil.Process(result['PID'])

        # Assert if the process is running
        assert process.is_running(), f"Process with PID {result['PID']} is not running."

        # Clean up

        # Kill the process after the check

        # time.sleep(15)   process kills also tensorboard directly after creating. if check if tensorbard gui is open unhashtag this line

        process = psutil.Process(result['PID'])
        # Recursively kill all child processes
        for child in process.children(recursive=True):
            child.kill()  # Force kill child processes

        # Kill the main process
        process.kill()

        # Remove logg folder
        folder_path_logs_out = BASE_DIR / "test_run" / "lightning_logs"

        if os.path.exists(str(folder_path_logs_out)):
            shutil.rmtree(str(folder_path_logs_out))
