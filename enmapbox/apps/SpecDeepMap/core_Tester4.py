import os
import glob

from qgis._core import QgsProcessingFeedback

import lightning as L
import numpy as np
import pandas as pd

from typing import Optional, List, ClassVar
import segmentation_models_pytorch as smp

import albumentations as A
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

from  enmapbox.apps.SpecDeepMap.core_DL_UNET50_MOD_15_059_16 import MyModel,model_2D_Justo_UNet_Simple,CustomDataset,preprocessing_imagenet, preprocessing_imagenet_additional, preprocessing_sentinel2_TOA,preprocessing_normalization_csv,get_preprocessing_pipeline, transforms_v2
from  enmapbox.apps.SpecDeepMap.core_PRED_GT_NO_DATA_mod11 import load_model_and_tile_size

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

    ###########################################no_data_value = maybe also do no data value (spectral image in advanced hyperparameter, fo maldefined images)
    if no_data_value != None:
        out_band.SetNoDataValue(no_data_value)
    out_raster.FlushCache()
    out_raster = None



def calculate_iou(pred, target, num_classes):

    ious = []
    for cls in range(1, num_classes+1):  # Start from class 1 to ignore class 0, as 1 classes is sum_classes-1 (ignpred zero class in onehot encoding),
                                         #########################   # add here +1 need adjust ment for case when not!!!!!
        intersection = np.logical_and(pred == cls, target == cls).sum()
        union = np.logical_or(pred == cls, target == cls).sum()
        if union == 0:
            ious.append(float('nan'))  # Handle cases where class is not present in both target and prediction
        else:
            ious.append(intersection / union)
    return ious


def process_images_from_csv(csv_file, model_checkpoint, acc_device=None, export_folder=None, csv_output_path=None,
                            no_data_label_mask=False, feedback: Optional[QgsProcessingFeedback] = None):

    acc_options = ['cpu', 'gpu']
    acc = acc_options[acc_device]
    model,_,_, num_classes,remove_c = load_model_and_tile_size(model_checkpoint, acc)


    df = pd.read_csv(csv_file)
    all_ious = []

    len_counter = len(df)
    if export_folder:
        len_counter = len(df) *2

    counter = 0

    print('remove',remove_c)


    for index, row in df.iterrows():

        if feedback and feedback.isCanceled():
            raise KeyboardInterrupt("Prediction process canceled by user.")

        image_path = row['image']
        mask_path = row['mask']  # Assuming a 'mask' column with ground truth paths

        # Read the image using GDAL, including the no-data mask
        image, geotransform, projection, no_data_value, no_data_mask = read_image_with_gdal(image_path)

        #print(no_data_value)
        # Create an empty prediction array for the entire image
        full_prediction = np.zeros((image.shape[1], image.shape[2]), dtype=np.uint8)

        # Assuming the image is in [channels, height, width] format and normalized
        image = np.expand_dims(image, axis=0)

        # Make prediction using the model
        image = image.astype(np.float32)

        preds = model.predict(image)

        preds = preds + 1   ## adjsut

        #preds  ## this doent work need different written parameter maybe string as false is not read from csv correctly
        #if remove_c == True:
            # No need to add +1
         #   preds = preds +1
        #else:
            # Add +1 to recover original labels
         #   preds = preds + 1
        ### add class count as start from 1 and not zero( )
            #preds = F.softmax(preds, dim=1)  # Get probabilities
            #pred_classes = torch.argmax(preds, dim=1).squeeze(0)  # Get predicted class for each pixel

        pred_np = preds.cpu().numpy().astype('uint8')

        # Store the predictions for this image
        full_prediction[:, :] = pred_np  # Directly copy the entire predicted image

        # Load the ground truth mask
        mask, _, _, _, _ = read_image_with_gdal(mask_path)


        # Overwrite predictions where the mask is 0 if `no_data_label_mask` is True
        if no_data_label_mask:
            full_prediction[mask == 0] = 0   # no_data_value

        # Calculate IoU per class
        ious = calculate_iou(full_prediction, mask, num_classes)
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
    mean_iou = np.nanmean(mean_iou_per_class)

    print(f"Mean IoU per class: {mean_iou_per_class}")
    print(f"Mean IoU across all classes: {mean_iou}")

    # Write IoU per class and mean IoU to a CSV file
    if csv_output_path:
        with open(csv_output_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Class', 'IoU'])

            # Write IoU for each class
            for cls, iou in enumerate(mean_iou_per_class, start =1):    ###### added start =1, to ignore class 0 and match with iou_calc_function adjust for when not given
                writer.writerow([cls, iou])

            # Write the mean IoU in the last row
            writer.writerow(['Mean IoU', mean_iou])

        print(f"IoU per class and mean IoU written to {csv_output_path}")

