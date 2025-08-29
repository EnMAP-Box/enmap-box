import glob
import os
import re
import unittest
from pathlib import Path

from processing.core.Processing import Processing

from enmapbox import DIR_UNITTESTS
from enmapbox.apps.SpecDeepMap import import_error
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase

if import_error is None:
    try:
        import lightning

        print(lightning)
    except Exception as error:
        import_error = error

if not import_error:
    import pandas as pd
    from enmapbox.apps.SpecDeepMap.processing_algorithm_tester import DL_Tester

    start_app()


def best_ckpt_path(checkpoint_dir):
    pattern = re.compile(r'val_iou_(\d+\.\d{4})')
    return max(
        (os.path.join(checkpoint_dir, f) for f in os.listdir(checkpoint_dir) if pattern.search(f)),
        key=lambda f: float(pattern.search(f).group(1))
    )


@unittest.skipIf(import_error, f'Missing modules to run SpecDeepMap: {import_error}')
class Test_Deep_Learning_Tester(TestCase):

    def test_dl_tester_iou(self):

        # init processing framework
        Processing.initialize()

        # run algorithm
        alg = DL_Tester()

        # Get the script's directory (makes paths relative)
        BASE_DIR = Path(__file__).parent

        BASE_TESTDATA = Path(DIR_UNITTESTS) / 'testdata/external/specdeepmap'

        folder_path_test_csv = BASE_TESTDATA / "test_requierments" / "test_files.csv"
        folder_path_test_iou = BASE_DIR / "test_run" / "test_iou.csv"
        folder_path_test_preds = BASE_DIR / "test_run" / "preds"
        checkpoint_dir = BASE_TESTDATA / "test_requierments"

        ckpt_path = best_ckpt_path(checkpoint_dir)

        io = {alg.P_test_data_csv: str(folder_path_test_csv),
              alg.P_model_checkpoint: str(ckpt_path),
              alg.P_acc_device: 0,
              alg.P_csv_output_tester: str(folder_path_test_iou),
              alg.P_folder_preds: str(folder_path_test_preds),
              alg.P_no_data_label_mask: True,
              }

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # 1. Test if Tester creates IoU csv and class count correctly
        # 1. Read CSV and Check for 6 Classes
        df = pd.read_csv(str(folder_path_test_iou))

        unique_classes = df['Class'].nunique()  # Count unique classes
        assert unique_classes == 6 + 1, f"Error: Expected 7 values, 6 classes and 1 mean but found 1 mean and {unique_classes}"

        # 2. Test if Tester predicts and exports
        tiff_files = glob.glob(f"{str(folder_path_test_preds)}/*.tif")
        tiff_len = len(tiff_files)  # List all .tif files
        assert tiff_len == 2, f"Error: Expected 2 tiff predicted & exported but found {tiff_len}"

        # After test clean up

        # Remove CSV
        if os.path.exists(str(folder_path_test_iou)):
            os.remove(str(folder_path_test_iou))

        # Remove Tiffs
        for tiff in tiff_files:
            os.remove(tiff)
