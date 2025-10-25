import os
import shutil
import time
import unittest
from pathlib import Path

import psutil

from enmapbox import DIR_UNITTESTS
from enmapbox.apps.SpecDeepMap import import_error
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from processing.core.Processing import Processing

if not import_error:
    from enmapbox.apps.SpecDeepMap.processing_algorithm_tensorboard_visualizer import Tensorboard_visualizer

    start_app()


@unittest.skipIf(import_error or TestCase.runsInCI(), f'Missing modules to run SpecDeepMap: {import_error}')
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

        process_exist = result['Process_exist']
        process_runs = result['process_runs']

        # Assert if the process is not existing or running
        assert process_exist is True or process_runs is True

        time.sleep(15)
        # if process still exist terminate
        cond = psutil.pid_exists(result['PID'])
        if cond is True:
            process = psutil.Process(result['PID'])
            # terminate possible childe process and main process
            for child in process.children(recursive=True):
                child.kill()
            process.kill()

        # Remove logg folder
        folder_path_logs_out = BASE_DIR / "test_run" / "lightning_logs"

        if os.path.exists(str(folder_path_logs_out)):
            shutil.rmtree(str(folder_path_logs_out))
