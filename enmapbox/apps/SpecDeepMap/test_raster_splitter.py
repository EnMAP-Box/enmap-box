from os.path import join, dirname
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing


from enmapbox.apps.SpecDeepMap.processingalgorithm_raster_splitter import RasterSplitter

from enmapbox import exampledata

import glob
from enmapboxprocessing.testcase import TestCase

class TestRasterSplitter(TestCase):

    def test_init(self):

      # init QGIS
      qgsApp = QgsApplication([], True)
      qgsApp.initQgis()
      qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

      # init processing framework
      Processing.initialize()

      # run algorithm
      alg = RasterSplitter()

      # Get the script's directory (makes paths relative)
      BASE_DIR = dirname(__file__)

      # Define paths using relative references
      input_l_path = join(BASE_DIR, "test_run/enmap_landcover_unstyled.tif")
      folder_path = join(BASE_DIR, "test_run/")
      folder_path_images = join(BASE_DIR, "test_run/images/")


      io = {alg.INPUT_I: exampledata.enmap,
            alg.INPUT_L: input_l_path,
            alg.P_tile_x: 32,
            alg.P_tile_y: 32,
            alg.P_step_x: 32,
            alg.P_step_y: 32,
            alg.Percent_null: 10,
            alg.P_OUTPUT_F: folder_path}

      result = Processing.runAlgorithm(alg, parameters=io)

      print(result)

       # Change to your folder path
      tif_files = glob.glob(f"{folder_path_images}/*.tif")
      num_tif_files = len(tif_files)# List all .tif files
      assert num_tif_files == 18, f"Error: Expected 18 .tif files, but found {num_tif_files}"
