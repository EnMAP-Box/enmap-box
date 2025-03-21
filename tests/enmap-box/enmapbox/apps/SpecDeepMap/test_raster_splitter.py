import glob
import os
import shutil
from pathlib import Path

from processing.core.Processing import Processing
from qgis.core import QgsProcessingAlgorithm

from enmapbox import DIR_UNITTESTS
from enmapbox import exampledata
from enmapbox.apps.SpecDeepMap.processing_algorithm_raster_splitter import RasterSplitter
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase

start_app()


class TestRasterSplitter(TestCase):

    def test_init(self):

        # init QGIS
        # qgsApp = QgsApplication([], True)
        # qgsApp.initQgis()
        # qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

        # init processing framework
        Processing.initialize()

        # run algorithm
        alg = RasterSplitter()
        self.assertIsInstance(alg, QgsProcessingAlgorithm)

        # Get the script's directory (makes paths relative)
        # Get the script's directory (makes paths relative)
        BASE_DIR = Path(__file__).parent

        BASE_TESTDATA = Path(DIR_UNITTESTS) / 'testdata/external/specdeepmap'

        folder_path_test_csv = BASE_TESTDATA / "test_requierments" / "test_files.csv"
        folder_path_test_iou = BASE_DIR / "test_run" / "test_iou.csv"
        folder_path_test_preds = BASE_DIR / "test_run" / "preds"
        checkpoint_dir = BASE_TESTDATA / "test_requierments"

        # Define paths using relative references
        input_l_path = BASE_TESTDATA / "test_requierments" / "enmap_landcover_unstyled.tif"
        folder_path = BASE_DIR / "test_run"

        folder_path_images = BASE_DIR / "test_run" / "images"

        io = {alg.INPUT_I: exampledata.enmap,
              alg.INPUT_L: str(input_l_path),
              alg.P_tile_x: 32,
              alg.P_tile_y: 32,
              alg.P_step_x: 32,
              alg.P_step_y: 32,
              alg.Percent_null: 10,
              alg.P_OUTPUT_F: str(folder_path)}

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # Change to your folder path
        tif_files = glob.glob(f"{str(folder_path_images)}/*.tif")
        num_tif_files = len(tif_files)  # List all .tif files
        assert num_tif_files == 18, f"Error: Expected 18 .tif files, but found {num_tif_files}"
        self.assertEqual(num_tif_files, 18, f"Error: Expected 18 .tif files, but found {num_tif_files}")

        # Clean up

        if os.path.exists(str(folder_path_images)):
            shutil.rmtree(str(folder_path_images))  # Deletes folder and all its contents
            print(f"Deleted folder: {str(folder_path_images)}")

        folder_path_labels = BASE_DIR / "test_run" / "labels"

        if os.path.exists(str(folder_path_labels)):
            shutil.rmtree(str(folder_path_labels))  # Deletes folder and all its contents
            print(f"Deleted folder: {str(folder_path_labels)}")
