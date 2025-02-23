from os.path import join, dirname
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing
import pandas as pd

from enmapbox.apps.SpecDeepMap.processingalgorithm_Tester4 import DL_Tester
from enmapbox.apps.SpecDeepMap.core_DL_UNET50_MOD_15_059_16_2 import MyModel
from enmapbox import exampledata
import glob
from enmapboxprocessing.testcase import TestCase
import lightning as L
import re
import os
import torch
from torchvision import transforms
from torchvision.transforms import v2
from osgeo import gdal

# need test data  & one checkpoint
# check if predict save tiff
# if iou matrix  created



def best_ckpt_path(checkpoint_dir):
    pattern = re.compile(r'val_iou_(\d+\.\d{4})')
    return max(
        (os.path.join(checkpoint_dir, f) for f in os.listdir(checkpoint_dir) if pattern.search(f)),
        key=lambda f: float(pattern.search(f).group(1))
    )


class Test_Deep_Learning_Tester(TestCase):

    def test_iou(self):

        # init QGIS
        qgsApp = QgsApplication([], True)
        qgsApp.initQgis()
        qgsApp.messageLog().messageReceived.connect(lambda *args: print(args[0]))

        # init processing framework
        Processing.initialize()

        # run algorithm
        alg = DL_Tester()

        # Get the script's directory (makes paths relative)
        BASE_DIR = dirname(__file__)


        folder_path_test_csv = join(BASE_DIR, "test_run/test_files.csv")
        folder_path_test_iou = join(BASE_DIR, "test_outs/test_iou.csv")
        folder_path_test_preds = join(BASE_DIR, "test_outs/")
        checkpoint_dir = join(BASE_DIR, "test_outs/")


        ckpt_path =best_ckpt_path(checkpoint_dir)

        io = {alg.P_test_data_csv: folder_path_test_csv,
                alg.P_model_checkpoint: ckpt_path,
                alg.P_acc_device:0,
                alg.P_csv_output_tester:folder_path_test_iou,
                alg.P_folder_preds:folder_path_test_preds,
                alg.P_no_data_label_mask: True,
                }

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # 1. Test if Tester creates IoU csv and class count correctly
        # 1. Read CSV and Check for 6 Classes
        df = pd.read_csv(folder_path_test_iou)

        unique_classes = df['Class'].nunique()  # Count unique classes
        assert unique_classes == 6 + 1 , f"Error: Expected 7 values, 6 classes and 1 mean but found 1 mean and {unique_classes}"

        # 2. Test if Tester predicts and exports
        tiff_files = glob.glob(f"{folder_path_test_preds}/*.tif")
        tiff_len = len(tiff_files)# List all .tif files
        assert tiff_len == 2, f"Error: Expected 2 tiff predicted & exported but found {tiff_len}"

        # After test clean up

        # Remove CSV
        if os.path.exists(folder_path_test_iou):
            os.remove(folder_path_test_iou)

        # Remove Tiffs
        for tiff in tiff_files:
            os.remove(tiff)
