from os.path import join, dirname
from qgis.core import QgsProcessingFeedback, QgsApplication
from processing.core.Processing import Processing
import pandas as pd

from enmapbox.apps.SpecDeepMap.processingalgorithm_PRED_GT_NO_DATA_mod11 import DL_Mapper
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
from osgeo import gdal, ogr

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
        alg = DL_Mapper()

        # Get the script's directory (makes paths relative)
        BASE_DIR = dirname(__file__)


        folder_path_pred_raster = join(BASE_DIR, "test_run/pred_raster.tif")
        folder_path_pred_iou = join(BASE_DIR, "test_outs/pred_iou.csv")
        folder_path_pred_vector = join(BASE_DIR, "test_run/pred_vector.shp")
        checkpoint_dir = join(BASE_DIR, "test_outs/")

        input_l_path = join(BASE_DIR, "test_run/enmap_landcover_unstyled.tif")

        ckpt_path =best_ckpt_path(checkpoint_dir)

        io = {alg.P_input_raster: exampledata.enmap,
                alg.P_model_checkpoint: ckpt_path,
                alg.P_gt_path: input_l_path,
                alg.P_overlap: 10,
                alg.P_acc: 0,
                alg.P_raster_output: folder_path_pred_raster,
                alg.P_vector_output: folder_path_pred_vector,
                alg.P_csv_output: folder_path_pred_iou,
                }

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # 1. Test if Mapper creates IoU csv and class count correctly
        # 1. Read CSV and Check for 6 Classes
        df = pd.read_csv(folder_path_pred_iou)

        unique_classes = df['Class'].nunique()  # Count unique classes
        assert unique_classes == 6 + 1 , f"Error: Expected 7 values, 6 classes and 1 mean but found 1 mean and {unique_classes}"


        # 2. Test if Mapper predicts and writes raster

        dataset = gdal.Open(folder_path_pred_raster)
        dataset_com = gdal.Open(exampledata.enmap)
        assert dataset is not None, f"Error: {folder_path_pred_raster} is not a valid raster file (couldn't be opened)."
        # Check if the raster has at least one band
        assert dataset.RasterCount > 0, f"Error: {folder_path_pred_raster} has no bands (not a valid raster)."
        # Check if the raster has valid dimensions
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        #assert width > 0 and height > 0, f"Error: {folder_path_pred_raster} has invalid dimensions ({width}x{height})."
        assert width == dataset_com.RasterXSize and height == dataset_com.RasterYSize, f"Error: {folder_path_pred_raster} has invalid dimensions ({width}x{height}), should have ({dataset_com.RasterXSize}x {dataset_com.RasterYSize})"

        dataset = None  # Close the dataset
        dataset_com = None


        #3. Test if Mapper converts prediction to vector file

        datasource = ogr.Open(folder_path_pred_vector)
        assert datasource is not None, f"Error: {folder_path_pred_vector} is not a valid vector file (couldn't be opened)."

        # Check if the vector has at least one layer
        assert datasource.GetLayerCount() > 0, f"Error: {folder_path_pred_vector} has no layers (invalid vector file)."

        # Check if the layer contains features
        layer = datasource.GetLayer(0)
        feature_count = layer.GetFeatureCount()
        assert feature_count > 0, f"Error: {folder_path_pred_vector} has no features (empty vector file)."

        datasource = None  # Close the datasource

        # After test clean up

        # Remove CSV
        #if os.path.exists(folder_path_pred_iou):
         #   os.remove(folder_path_pred_iou)

        #if os.path.exists(folder_path_pred_raster):
         #   os.remove(folder_path_pred_raster)

        #if os.path.exists(folder_path_pred_vector):
         #   os.remove(folder_path_pred_vector)
