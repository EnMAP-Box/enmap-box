import glob
import os
import unittest
from os.path import join
from pathlib import Path

from enmapbox import DIR_UNITTESTS
from enmapbox.apps.SpecDeepMap import import_error
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from processing.core.Processing import Processing

if import_error is None:
    try:
        import lightning

        print(lightning)
    except Exception as error:
        import_error = error

if not import_error:
    import pandas as pd
    from enmapbox.apps.SpecDeepMap.processing_algorithm_dataset_maker import DatasetMaker

    start_app()

BASE_TESTDATA = Path(DIR_UNITTESTS) / 'testdata/external/specdeepmap'


# BASE_DIR = Path(__file__).parent


@unittest.skipIf(import_error, f'Missing modules to run SpecDeepMap: {import_error}')
class Test_Dataset_Maker(TestCase):

    def test_init(self):

        # init QGIS
        # qgsApp = QgsApplication([], True)
        # qgsApp.initQgis()
        # qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

        # init processing framework
        Processing.initialize()

        # run algorithm
        alg = DatasetMaker()

        # Get the script's directory (makes paths relative)
        # BASE_DIR = dirname(__file__)

        folder_path_in = BASE_TESTDATA / 'test_requierments'
        folder_path_out = self.createTestOutputDirectory().as_posix()

        io = {alg.Train_Val_folder: str(folder_path_in),
              alg.N_train: 80,
              alg.N_test: 10,
              alg.N_val: 10,
              alg.Seed: 42,
              alg.scaler: 10000,
              alg.normalize: True,
              alg.N_permute: 100,
              alg.Output_path: str(folder_path_out)}

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # 1 Test all Csv files created
        csv_files = glob.glob(f"{folder_path_out}/*.csv")
        num_csv_files = len(csv_files)  # List all .tif files
        assert num_csv_files == 5, f"Error: Expected 18 .tif files, but found {num_csv_files}"

        # 2 Test split correct Train, Test, Val

        csv_files = {
            "train_files.csv": 14,
            "test_files.csv": 2,
            "validation_files.csv": 2
        }

        # Loop through each CSV file and check the row count
        for csv_file, expected_count in csv_files.items():
            path_csv_file = join(folder_path_out, csv_file)
            df = pd.read_csv(path_csv_file)

            row_count = df['image'].count()
        assert row_count == expected_count, f"Error: Expected {expected_count} .tif files in {csv_file}, but found {row_count}"

        # 3 add test summary csv

        # 4 add test normalization

        # Clean up

        if os.path.exists(folder_path_out):
            for file in os.listdir(folder_path_out):
                if file.endswith(".csv"):
                    file_path_out = os.path.join(folder_path_out, file)
                    os.remove(file_path_out)
