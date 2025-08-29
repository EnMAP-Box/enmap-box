import os
import re
import unittest
from pathlib import Path

from osgeo import gdal, ogr
from processing.core.Processing import Processing

from enmapbox import DIR_UNITTESTS, exampledata
from enmapbox.apps.SpecDeepMap import import_error
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase

try:
    import lightning
except Exception as error:
    import_error = error

if not import_error:
    import pandas as pd
    from enmapbox.apps.SpecDeepMap.processing_algorithm_deep_learning_mapper import DL_Mapper

    start_app()

try:
    import lightning
except Exception as error:
    import_error = error


def best_ckpt_path(checkpoint_dir):
    pattern = re.compile(r'val_iou_(\d+\.\d{4})')
    return max(
        (os.path.join(checkpoint_dir, f) for f in os.listdir(checkpoint_dir) if pattern.search(f)),
        key=lambda f: float(pattern.search(f).group(1))
    )


BASE_TESTDATA = Path(DIR_UNITTESTS) / 'testdata/external/specdeepmap'
BASE_DIR = Path(__file__).parent


@unittest.skipIf(import_error, f'Missing modules to run SpecDeepMap: {import_error}')
class Test_Deep_Learning_Mapper(TestCase):

    def test_iou_mapper(self):

        # init processing framework
        Processing.initialize()

        # run algorithm
        alg = DL_Mapper()

        # Get the script's directory (makes paths relative)
        # BASE_DIR = dirname(__file__)

        folder_path_pred_raster = BASE_DIR / "pred_raster.tif"
        folder_path_pred_iou = BASE_DIR / "pred_iou.csv"
        folder_path_pred_vector = BASE_DIR / "pred_vector.shp"

        checkpoint_dir = BASE_TESTDATA / "test_requierments"
        input_l_path = BASE_TESTDATA / "test_requierments" / "enmap_landcover_unstyled.tif"

        ckpt_path = best_ckpt_path(checkpoint_dir)

        io = {alg.P_input_raster: exampledata.enmap,
              alg.P_model_checkpoint: str(ckpt_path),
              alg.P_gt_path: str(input_l_path),
              alg.P_overlap: 10,
              alg.P_acc: 0,
              alg.P_raster_output: str(folder_path_pred_raster),
              alg.P_vector_output: str(folder_path_pred_vector),
              alg.P_csv_output: str(folder_path_pred_iou),
              }

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # 1. Test if Mapper creates IoU csv and class count correctly
        # 1. Read CSV and Check for 6 Classes
        df = pd.read_csv(str(folder_path_pred_iou))

        unique_classes = df['Class'].nunique()  # Count unique classes
        assert unique_classes == 6 + 1, f"Error: Expected 7 values, 6 classes and 1 mean but found 1 mean and {unique_classes}"

        # 2. Test if Mapper predicts and writes raster

        dataset = gdal.Open(str(folder_path_pred_raster))
        dataset_com = gdal.Open(exampledata.enmap)
        assert dataset is not None, f"Error: {str(folder_path_pred_raster)} is not a valid raster file (couldn't be opened)."
        # Check if the raster has at least one band
        assert dataset.RasterCount > 0, f"Error: {str(folder_path_pred_raster)} has no bands (not a valid raster)."
        # Check if the raster has valid dimensions
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        # assert width > 0 and height > 0, f"Error: {folder_path_pred_raster} has invalid dimensions ({width}x{height})."
        assert width == dataset_com.RasterXSize and height == dataset_com.RasterYSize, f"Error: {str(folder_path_pred_raster)} has invalid dimensions ({width}x{height}), should have ({dataset_com.RasterXSize}x {dataset_com.RasterYSize})"

        dataset = None  # Close the dataset
        dataset_com = None

        # 3. Test if Mapper converts prediction to vector file

        datasource = ogr.Open(str(folder_path_pred_vector))
        assert datasource is not None, f"Error: {str(folder_path_pred_vector)} is not a valid vector file (couldn't be opened)."

        # Check if the vector has at least one layer
        assert datasource.GetLayerCount() > 0, f"Error: {str(folder_path_pred_vector)} has no layers (invalid vector file)."

        # Check if the layer contains features
        layer = datasource.GetLayer(0)
        feature_count = layer.GetFeatureCount()
        assert feature_count > 0, f"Error: {str(folder_path_pred_vector)} has no features (empty vector file)."

        datasource = None  # Close the datasource

        # After test clean up

        # Remove CSV
        # if os.path.exists(folder_path_pred_iou):
        #   os.remove(folder_path_pred_iou)
        # Remove tif
        if os.path.exists(str(folder_path_pred_raster)):
            os.remove(str(folder_path_pred_raster))

        # Remove shp
        base_name = os.path.splitext(str(folder_path_pred_vector))[0]

        # List of extensions to remove
        extensions = ['.shp', '.shx', '.dbf', '.prj']

        # Remove each file if it exists
        for ext in extensions:
            file_path = base_name + ext
            if os.path.exists(file_path):
                os.remove(file_path)
            # os.remove(folder_path_pred_vector)

        # Remove CSV
        if os.path.exists(str(folder_path_pred_iou)):
            os.remove(str(folder_path_pred_iou))
