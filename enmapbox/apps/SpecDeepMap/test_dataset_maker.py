from os.path import join, dirname
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing
import pandas as pd

from enmapbox.apps.SpecDeepMap.processing_algorithm_dataset_maker import DatasetMaker

from enmapbox import exampledata

import glob
from enmapboxprocessing.testcase import TestCase

class Test_Dataset_Maker(TestCase):

    def test_init(self):

      # init QGIS
      qgsApp = QgsApplication([], True)
      qgsApp.initQgis()
      qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

      # init processing framework
      Processing.initialize()

      # run algorithm
      alg = DatasetMaker()

      # Get the script's directory (makes paths relative)
      BASE_DIR = dirname(__file__)

      folder_path = join(BASE_DIR, "test_run/")


      io = {alg.Train_Val_folder: folder_path,
            alg.N_train:80,
            alg.N_test: 10,
            alg.N_val: 10,
            alg.Seed: 42,
            alg.scaler: 10000,
            alg.normalize: True,
            alg.N_permute: 100,
            alg.Output_path: folder_path}

      result = Processing.runAlgorithm(alg, parameters=io)

      print(result)

       # 1 Test all Csv files created
      csv_files = glob.glob(f"{folder_path}/*.csv")
      num_csv_files = len(csv_files)# List all .tif files
      assert num_csv_files == 5, f"Error: Expected 18 .tif files, but found {num_csv_files}"

      # 2 Test split correct Train, Test, Val

      csv_files = {
          "train_files.csv": 14,
          "test_files.csv": 2,
          "validation_files.csv": 2
      }

      # Loop through each CSV file and check the row count
      for csv_file, expected_count in csv_files.items():
          path_csv_file = join(folder_path, csv_file)
          df = pd.read_csv(path_csv_file)

          row_count = df['image'].count()
          assert row_count == expected_count, f"Error: Expected {expected_count} .tif files in {csv_file}, but found {row_count}"

      # 3 add test summary csv





      # 4 add test normalization