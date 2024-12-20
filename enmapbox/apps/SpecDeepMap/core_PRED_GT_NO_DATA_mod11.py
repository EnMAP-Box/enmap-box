import os
import glob

from qgis._core import QgsProcessingFeedback
from torch.utils import data
import lightning as L
import numpy as np
import pandas as pd
from torchmetrics import JaccardIndex
from lightning.pytorch.loggers import TensorBoardLogger
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping
from typing import Optional, List, ClassVar
import segmentation_models_pytorch as smp
import torch
import albumentations as A
from torch.utils.data import Dataset
from osgeo import gdal
from osgeo import ogr


# CPU vs GPU, MSE And CE

import csv

#import pytorch_lightning as pl
import segmentation_models_pytorch as smp
import torch

from torch.utils.data import Dataset


import torch.nn as nn
import torch.nn.functional as F

from typing_extensions import ClassVar
from typing import Optional
import torchmetrics
from torchmetrics import JaccardIndex
from torchmetrics.classification import BinaryJaccardIndex
from lightning.pytorch.loggers import TensorBoardLogger
from lightning.pytorch.callbacks import LearningRateFinder
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping

from torchvision.transforms import v2

from qgis._core import QgsProcessingFeedback


from  enmapbox.apps.SpecDeepMap.core_DL_UNET50_MOD_15_059_16 import MyModel,CustomDataset,preprocessing_imagenet, preprocessing_imagenet_additional,preprocessing_sentinel2_TOA,preprocessing_normalization_csv,get_preprocessing_pipeline, transforms_v2


from torchvision import transforms
from torch import nn
import torch
from torchvision import transforms

import math
from osgeo import gdal, ogr, osr
from torchvision.transforms import Compose, ToTensor

# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 11:40:42 2024

@author: leon-
"""

import os
import numpy as np
import torch
from sklearn.metrics import jaccard_score
import csv
from osgeo import gdal, ogr, osr




def load_model_and_tile_size(model_checkpoint, acc):

    # Load the model checkpoint
    checkpoint = torch.load(model_checkpoint, map_location=torch.device(acc))

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
            "preprocess":pre_process
        }
    )

    # Set the model to evaluation mode
    model.eval()

    # Return the model and tile sizes
    return model, tile_size_x, tile_size_y , num_classes, remove_c


def raster_to_vector(out_ds, vector_output, no_data_value):

    # Get the first band of the raster dataset
    raster_band = out_ds.GetRasterBand(1)

    # Fetch the projection from the raster dataset
    raster_projection = out_ds.GetProjection()

    # Create a new Shapefile
    driver = ogr.GetDriverByName("ESRI Shapefile")


    # Create the new vector data source (Shapefile)
    ##########################################################################

    directory = os.path.dirname(vector_output)
    if not os.path.exists(directory):
        os.makedirs(directory)

    vector_ds = driver.CreateDataSource(vector_output)

    # Set the spatial reference from the raster's projection
    spatial_ref = osr.SpatialReference()
    if raster_projection != '':
        spatial_ref.ImportFromWkt(raster_projection)

    # Create a new layer for the polygons
    layer = vector_ds.CreateLayer(vector_output, spatial_ref, geom_type=ogr.wkbPolygon)

    # Create a new field for the "Class" (or category) values from the raster
    field_name = ogr.FieldDefn("Class", ogr.OFTInteger)
    layer.CreateField(field_name)

    # Perform the polygonization (raster-to-vector conversion)
    gdal.Polygonize(raster_band, None, layer, 0, [], callback=None)

    # Remove features where the "Class" field equals the no_data_value
    layer.StartTransaction()
    for feature in layer:
        if feature.GetField("Class") == no_data_value:
            layer.DeleteFeature(feature.GetFID())
    layer.CommitTransaction()

    # Clean up and save the shapefile
    vector_ds = None  # Close the dataset to ensure it is properly saved
    print(f"Conversion to vector completed and saved at {vector_output}.")



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


def generate_positions(image_dim, tile_dim, stride):
    positions = []
    pos = 0
    while pos < image_dim - tile_dim:
        positions.append(pos)
        pos += stride

    # Check if the last tile (image_dim - tile_dim) overlaps entirely with the previous tile
    if positions and (positions[-1] + tile_dim < image_dim):
        positions.append(image_dim - tile_dim)  # Only add if the last tile isn't already covering the end

    return positions


def calculate_stride_and_overlap(tile_size_x, tile_size_y, overlap_percentage):
    """
    overlap_percentage: The overlap percentage on each side.

    """
    # Convert overlap percentage to a fraction
    overlap = overlap_percentage / 100

    # Calculate stride (step size) for positioning tiles, reducing by 2 * overlap
    stride_x = int(tile_size_x * (1 - overlap * 2))  # Stride in the x direction
    stride_y = int(tile_size_y * (1 - overlap * 2))  # Stride in the y direction

    # Calculate overlap in pixels for cropping on both sides
    overlap_x = int(tile_size_x * overlap)  # Overlap in x direction
    overlap_y = int(tile_size_y * overlap)  # Overlap in y direction

    return stride_x, stride_y, overlap_x, overlap_y


def pred_mapper(input_raster=None, model_checkpoint=None, overlap=10, gt_path=None, ignore_index=0
         , acc=None, raster_output=None, vector_output=None, csv_output=None,
         feedback: QgsProcessingFeedback = None):  # , #vector=True
    # get names

    print('vector_output',  vector_output)

    acc_options = ['cpu', 'gpu']
    acc = acc_options[acc]
    base_name = os.path.basename(input_raster)

    # Split the base name into name and extension
    name, ext = os.path.splitext(base_name)

    print(gt_path)
    # Open the dataset
    dataset = gdal.Open(input_raster)

    image_x = dataset.RasterXSize
    image_y = dataset.RasterYSize
    print('x_image_size', image_x, 'y_image_size', image_y)

    # Select the first band (index 1) and get no data value
    band = dataset.GetRasterBand(1)
    no_data_value = band.GetNoDataValue()

    # Create an in-memory raster
    driver = gdal.GetDriverByName('MEM')
    mem_ds = driver.Create('', image_x, image_y, 1, gdal.GDT_Float32)
    mem_ds.SetGeoTransform(dataset.GetGeoTransform())
    mem_ds.SetProjection(dataset.GetProjection())

    ### added read image x and y from checkpoint

    model, tile_size_x, tile_size_y, num_classes, remove_c = load_model_and_tile_size(model_checkpoint, acc=acc)


    stride_x, stride_y, overlap_x, overlap_y = calculate_stride_and_overlap(tile_size_x, tile_size_y,
                                                                            overlap_percentage=overlap)

    print(stride_x, stride_y, overlap_x, overlap_y)

    ###### generate positions

    x_positions = generate_positions(image_x, tile_size_x, stride_x)
    y_positions = generate_positions(image_y, tile_size_y, stride_y)
    print('X_positions', x_positions)
    print('Y_positions', y_positions)
    total_tiles = len(x_positions) * len(y_positions)

    # Initialize the counter
    counter = 0

    for x in x_positions:
        for y in y_positions:
            tile = dataset.ReadAsArray(x, y, tile_size_x, tile_size_y)

            image = np.expand_dims(tile, axis=0)


            # Make prediction using the model
            image = image.astype(np.float32)


            preds = model.predict(image)

            preds = preds +1

            #if remove_c == True:
             #   # No need to add +1   but some yes, because of model loader encoding!!!!!!!!!!!!!!!!!!!!! could just be preds +1 no if needed
              #  preds = preds +1
            #else:
                # Add +1 to recover original labels
             #   preds = preds +1
                 ###### added as now predict values from 0-5 and want 1-6 instead + added in model description prediction

            #####################################################################################

            pred_classes = preds.squeeze(0)  # Shape becomes [H, W]

            # Convert to numpy for further use outside PyTorch
            pred_flat = pred_classes.detach().numpy().astype("uint8")

            # Determine crop coordinates within the tile
            if x == 0:
                x_start = 0
                x_end = tile_size_x - overlap_x
            elif x == x_positions[-1]:
                x_start = overlap_x
                x_end = tile_size_x
            else:
                x_start = overlap_x
                x_end = tile_size_x - overlap_x

            if y == 0:
                y_start = 0
                y_end = tile_size_y - overlap_y
            elif y == y_positions[-1]:
                y_start = overlap_y
                y_end = tile_size_y
            else:
                y_start = overlap_y
                y_end = tile_size_y - overlap_y

            # Crop the tile
            cropped = pred_flat[y_start:y_end,
                      x_start:x_end]

            # Write the cropped tile back, adjusting for overlap in the output coordinates
            output_x = x if x == 0 else x + overlap_x
            output_y = y if y == 0 else y + overlap_y
            mem_ds.GetRasterBand(1).WriteArray(cropped, xoff=output_x, yoff=output_y)

            counter += 1

            progress = (counter / total_tiles) * 100
            if isinstance(feedback, QgsProcessingFeedback):
                feedback.setProgress(progress)

                # Allow user to cancel the process
                if feedback.isCanceled():
                    break


     # no_data_value = 0 #################in case images have no data value bad defined maybe , add as optional advanced hyperparameter in gui
    if no_data_value != None:
    # dataset = gdal.Open(input_raster)
        modified_band = dataset.GetRasterBand(1)

        # Read data from modified raster
        data_arr = modified_band.ReadAsArray()
        # data_arr = dataset.ReadAsArray(0)

        # create mask for no-data values
        mask = (data_arr == no_data_value)

        mem_arr = mem_ds.ReadAsArray()  # assuming a single band raster

        #mask image
        mem_arr[mask] = no_data_value

        #write masked image to ratser file
        mem_ds.WriteArray(mem_arr)


    ## new
        band = mem_ds.GetRasterBand(1)
        band.SetNoDataValue(no_data_value)

    #######################ified here  does it agan  harmoize with no-data function
    if gt_path:
        gt_dataset = gdal.Open(gt_path)
        gt_data_arr = gt_dataset.ReadAsArray()

        gt_mask = (gt_data_arr == 0)

        mem_arr = mem_ds.ReadAsArray()  # assuming a single band raster

        #mask image
        mem_arr[gt_mask] = 0

        #write masked image to ratser file
        mem_ds.WriteArray(mem_arr)


    ## new
        band = mem_ds.GetRasterBand(1)
        band.SetNoDataValue(0)  #### hardcoded 0 as no data

    gtiff_driver = gdal.GetDriverByName('GTiff')
    out_ds = gtiff_driver.CreateCopy(raster_output, mem_ds, 0)

    # vectorize raster  (drop no data polygon, (outside bounds))
    if vector_output:
        raster_to_vector(out_ds, vector_output, no_data_value)

    # calc. mean and per class IoU ignore index (no-data label))


    if gt_path:
            # Open the ground truth raster
        gt_dataset = gdal.Open(gt_path)
        gt = gt_dataset.ReadAsArray()
        print('Ground truth raster shape:', gt.shape)

            # Open the prediction raster
        pred_dataset = mem_ds
        prediction = pred_dataset.ReadAsArray()

            # Ensure shapes match
        if gt.shape != prediction.shape:
            raise ValueError(f"Shape mismatch: ground truth {gt.shape} and prediction {prediction.shape}")

        print('num_classes',num_classes)

            # Calculate IoU per class
        ious = compute_iou_per_class(prediction, gt, num_classes)
        print(f"Mean IoU per class: {ious}")

        mean_iou = np.nanmean(ious)
        print(f"Mean IoU across all classes: {mean_iou}")

            # Write IoU per class and mean IoU to a CSV
        if csv_output:
            with open(csv_output, mode='w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['Class', 'IoU'])

                    # Write IoU for each class
                for cls, iou in enumerate(ious, start=0):   ##########################  need change if background class zero was removed or not
                    writer.writerow([cls, iou])

                    # Write the mean IoU in the last row
                writer.writerow(['Mean IoU', mean_iou])

            print(f"IoU per class and mean IoU written to {csv_output}")

    mem_ds = None
    out_ds = None
    dataset = None
    modified_band = None
    modified_dataset = None


