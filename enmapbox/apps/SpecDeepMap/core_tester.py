import os
import glob

from qgis._core import QgsProcessingFeedback

import lightning as L
import numpy as np
import pandas as pd

from typing import Optional, List, ClassVar
import segmentation_models_pytorch as smp

#import albumentations as A
from torch.utils.data import Dataset

import csv

import math
from osgeo import gdal, ogr, osr

from typing_extensions import ClassVar

from typing import Optional
import torch
from torch.utils import data
from torch import nn
import torch.nn.functional as F
import torchmetrics
from torchmetrics import JaccardIndex
from torchmetrics.classification import BinaryJaccardIndex
from lightning.pytorch.loggers import TensorBoardLogger
from lightning.pytorch.callbacks import LearningRateFinder
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping
from torchvision.transforms import Compose, ToTensor
from torchvision import transforms


from torchvision.transforms import v2

from enmapbox.apps.SpecDeepMap.core_deep_learning_trainer import MyModel,model_2D_Justo_UNet_Simple,CustomDataset,preprocessing_imagenet, preprocessing_imagenet_additional, preprocessing_sentinel2_TOA,preprocessing_normalization_csv,get_preprocessing_pipeline, transforms_v2
from enmapbox.apps.SpecDeepMap.core_deep_learning_mapper import load_model_and_tile_size

from qgis._core import QgsProcessingFeedback
def compute_iou(pred, gt, class_id):
    """Compute IoU for a single class."""
    intersection = np.logical_and(pred == class_id, gt == class_id).sum()
    union = np.logical_or(pred == class_id, gt == class_id).sum()
    if union == 0:
        return 0
    else:
        return intersection / union



### Data augmentation

transforms_v2 = v2.Compose([
    v2.RandomRotation(degrees=45),
    v2.RandomHorizontalFlip(p=0.5),
    v2.RandomVerticalFlip(p=0.5),
])


def load_model_and_tile_size(model_checkpoint, acc):
    # Load the model checkpoint
    checkpoint = torch.load(model_checkpoint, map_location=torch.device(acc), weights_only=False)

    # Retrieve hyperparameters from the checkpoint
    hyperpara = checkpoint['hyper_parameters']

    # Extract tile size and other relevant hyperparameters
    tile_size_x = hyperpara['img_x']
    tile_size_y = hyperpara['img_y']
    num_classes = hyperpara['classes']

    in_channels = hyperpara["in_channels"]
    architecture_used = hyperpara['architecture']
    backbone_used = hyperpara['backbone']
    pre_process = hyperpara['preprocess']
    remove_c = hyperpara['remove_background_class']

    # Load the model with the extracted hyperparameters
    model = MyModel.load_from_checkpoint(
        model_checkpoint,
        hparams={
            "architecture": architecture_used,
            "backbone": backbone_used,
            "transform": None,
            "class_weights_balanced": False,
            "acc_type": acc,
            "batch_size": 1,
            "classes": num_classes,
            "in_channels": in_channels,
            "preprocess": pre_process,
            'remove_background_class':remove_c
        }
    )

    # Set the model to evaluation mode
    model.eval()

    # Return the model and tile sizes
    return model, tile_size_x, tile_size_y, num_classes, remove_c



def read_image_with_gdal(image_path):

    dataset = gdal.Open(image_path)

    # channel first
    data_array = dataset.ReadAsArray().astype(np.float32)

    image = dataset.ReadAsArray()  # Automatically reads all bands
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    no_data_value = dataset.GetRasterBand(1).GetNoDataValue()


    # Create a no-data mask for the first band
    no_data_mask = None

    if no_data_value is not None:
        #no_data_mask = image[0] == no_data_value

        first_band = dataset.GetRasterBand(1)
        nodata_first_band = first_band.GetNoDataValue()

        # Read data from modified raster
        nodata_first_band_arr = first_band.ReadAsArray()
        # data_arr = dataset.ReadAsArray(0)

        no_data_mask = ( nodata_first_band_arr == nodata_first_band)


    dataset = None  # Close the GDAL dataset
    return image, geotransform, projection, no_data_value, no_data_mask


def save_prediction_as_geotiff(pred_array, geotransform, projection, output_path, no_data_value, no_data_mask):

    driver = gdal.GetDriverByName('GTiff')
    out_raster = driver.Create(output_path, pred_array.shape[1], pred_array.shape[0], 1, gdal.GDT_Byte)
    out_raster.SetGeoTransform(geotransform)
    out_raster.SetProjection(projection)
    out_band = out_raster.GetRasterBand(1)

    out_band.WriteArray(pred_array)

    if no_data_value != None:
        out_band.SetNoDataValue(no_data_value)
    out_raster.FlushCache()
    out_raster = None



def compute_iou_per_class(pred, gt, num_classes):
    """Compute IoU for each class."""
    ious = []
    for cls in range(num_classes):
        pred_cls = (pred == cls)
        gt_cls = (gt == cls)
        intersection = np.logical_and(pred_cls, gt_cls).sum()
        union = np.logical_or(pred_cls, gt_cls).sum()
        if union == 0:
            ious.append(np.nan)  # Avoid dividing by zero
        else:
            ious.append(intersection / union)
    return ious

def process_images_from_csv(csv_file, model_checkpoint, acc_device=None, export_folder=None, csv_output_path=None,
                            no_data_label_mask=False, feedback: Optional[QgsProcessingFeedback] = None):

    acc_options = ['cpu', 'gpu']
    acc = acc_options[acc_device]
    model,_,_, num_classes,remove_c = load_model_and_tile_size(model_checkpoint, acc)

    print(num_classes)
    df = pd.read_csv(csv_file)
    all_ious = []

    len_counter = len(df)
    if export_folder:
        len_counter = len(df) *2

    counter = 0

    print('remove',remove_c)

    # variables to check zero presence in mask, if yes first class in iou count is skipped and num_classes is extended by 1
    Zero_in_mask = False
    #b = 0

    for index, row in df.iterrows():

        if feedback and feedback.isCanceled():
            raise KeyboardInterrupt("Prediction process canceled by user.")

        image_path = row['image']
        mask_path = row['mask']  # Assuming a 'mask' column with ground truth paths

        # Read the image using GDAL, including the no-data mask
        image, geotransform, projection, no_data_value, no_data_mask = read_image_with_gdal(image_path)

        # Create an empty prediction array for the entire image
        full_prediction = np.zeros((image.shape[1], image.shape[2]), dtype=np.uint8)

        # Assuming the image is in [channels, height, width] format and normalized
        image = np.expand_dims(image, axis=0)

        # Make prediction using the model
        image = image.astype(np.float32)

        preds = model.predict(image)

        preds = preds + 1   ## adjsut

        pred_np = preds.cpu().numpy()

        # Store the predictions for this image
        full_prediction[:, :] = pred_np  # Directly copy the entire predicted image

        # Load the ground truth mask
        mask, _, _, _, _ = read_image_with_gdal(mask_path)

        # Overwrite predictions where the mask is 0 if `no_data_label_mask` is True

        full_prediction_iou = full_prediction[mask == 0] = 0   # no_data_value

        # Calculate IoU per class
        ious = compute_iou_per_class(full_prediction_iou, mask, num_classes)
        print(ious)
        all_ious.append(ious)

        # count first loop
        counter += 1

        if feedback:
            progress = (counter / len_counter) * 100
            feedback.setProgress(progress)

        # Export the prediction as a georeferenced GeoTIFF if export_folder is provided
        if export_folder:

            if no_data_mask is not None:
                full_prediction[no_data_mask] = 0 ######no_data_value
            # Create the output file path, using the original image filename with '_prediction' added
            original_filename = os.path.basename(image_path)
            output_filename = os.path.splitext(original_filename)[0] + '_prediction.tif'
            output_path = os.path.join(export_folder, output_filename)

            save_prediction_as_geotiff(full_prediction, geotransform, projection, output_path, no_data_value,
                                       no_data_mask)
            print(f"Exported prediction to {output_path}")
            counter +=1
            if feedback:
                progress = (counter / len_counter) * 100
                feedback.setProgress(progress)


    # Calculate the mean IoU across all images for each class
    mean_iou_per_class = np.nanmean(all_ious, axis=0)

    # different approach here compared to mapper. if remove = yes meaning automatical 0 in data as otherwise  remove_c no: meaning no class extension needed
    # inmapper
    if remove_c == 'Yes':
        mean_iou = np.nanmean(mean_iou_per_class[1:])  # Skip class 0
        b = 1
    else:
        mean_iou = np.nanmean(mean_iou_per_class)  # Include all classes
        b = 0

    #mean_iou = np.nanmean(mean_iou_per_class)

    print(f"Mean IoU per class: {mean_iou_per_class}")
    print(f"Mean IoU across all classes: {mean_iou}")

    # Write IoU per class and mean IoU to a CSV file
    if csv_output_path:
        with open(csv_output_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Class', 'IoU'])

            # Write IoU for each class
            for cls, iou in enumerate(mean_iou_per_class[b:], start =b):
                writer.writerow([cls, iou])

            # Write the mean IoU in the last row
            writer.writerow(['Mean IoU', mean_iou])

        print(f"IoU per class and mean IoU written to {csv_output_path}")

