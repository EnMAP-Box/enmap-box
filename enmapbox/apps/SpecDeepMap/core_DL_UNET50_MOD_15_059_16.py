
import os
import glob
import math
from qgis._core import QgsProcessingFeedback
from torch.utils import data
import lightning as L
import numpy as np
import pandas as pd
from torchmetrics import JaccardIndex
from typing import Optional, List, ClassVar
import albumentations as A
from torch.utils.data import Dataset
from osgeo import gdal

import subprocess

from lightning.pytorch.tuner import Tuner
import segmentation_models_pytorch as smp
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset
from osgeo import gdal  # Import the gdal module
from typing_extensions import ClassVar

from typing import Optional

import torchmetrics
from torchmetrics import JaccardIndex
from torchmetrics.classification import BinaryJaccardIndex
from lightning.pytorch.loggers import TensorBoardLogger
from lightning.pytorch.callbacks import LearningRateFinder
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping

from torchvision.transforms import v2
from torchvision import transforms
from enmapbox.apps.SpecDeepMap.resnet_mod import ResNet18_Weights, ResNet50_Weights
import utils




from qgis._core import QgsProcessingFeedback

### Data augmentation

transforms_v2 = v2.Compose([
    v2.RandomRotation(degrees=45),
    v2.RandomHorizontalFlip(p=0.5),
    v2.RandomVerticalFlip(p=0.5),
])


from segmentation_models_pytorch.encoders import get_preprocessing_fn

#preprocess_input = get_preprocessing_fn('resnet18', pretrained='imagenet')


from torchvision.models._api import Weights, WeightsEnum


_model_weights = {
    "Sentinel_2_TOA_Resnet18": [ResNet18_Weights.SENTINEL2_ALL_MOCO],
    "Sentinel_2_TOA_Resnet50": [ResNet50_Weights.SENTINEL2_ALL_MOCO],
    "LANDSAT_TM_TOA_Resnet18": [ResNet18_Weights.LANDSAT_TM_TOA_MOCO],
    "LANDSAT_ETM_TOA_Resnet18": [ResNet18_Weights.LANDSAT_ETM_TOA_MOCO],
    "LANDSAT_OLI_TIRS_TOA_Resnet18": [ResNet18_Weights.LANDSAT_OLI_TIRS_TOA_MOCO],
    "LANDSAT_ETM_SR_Resnet18": [ResNet18_Weights.LANDSAT_ETM_SR_MOCO],
    "LANDSAT_OLI_SR_Resnet18": [ResNet18_Weights.LANDSAT_OLI_SR_MOCO],
}
def get_weight(name: str) -> WeightsEnum:
    """Get the weights enum value by its full name.

    .. versionadded:: 0.4

    Args:
        name: Name of the weight enum entry.

    Returns:
        The requested weight enum.

    Raises:
        ValueError: If *name* is not a valid WeightsEnum.


    """
    if name is None:
        return None
        
    for weight_name, weight_enum in _model_weights.items():
        if isinstance(weight_name, str):
            for sub_weight_enum in weight_enum:
                if name == str(sub_weight_enum):
                    return sub_weight_enum

    raise ValueError(f'{name} is not a valid WeightsEnum')

    




def preprocessing_imagenet():
    # Read the CSV into a pandas DataFrame

    # ImageNet BGR mean values (reversed RGB values)
    imagenet_bgr_mean = [0.406, 0.456, 0.485]  # BGR order
    imagenet_bgr_stds = [0.229, 0.224, 0.225]

    # Create and return the PyTorch normalization transform
    return transforms.Compose([
        #transforms.ToTensor(),  # Convert the image to a PyTorch tensor
        transforms.Normalize(mean=imagenet_bgr_mean, std=imagenet_bgr_stds)  # Normalize using the modified means and stds
    ])


def preprocessing_imagenet_additional(csv_path):
    # Read the CSV into a pandas DataFrame
    data = pd.read_csv(csv_path)

    # Extract the 'mean' column from the CSV, assuming it has a 'mean' column
    all_means = data['mean'].tolist()

    # ImageNet BGR mean values (reversed RGB values)
    imagenet_bgr_mean = [0.406, 0.456, 0.485]  # BGR order
    imagenet_bgr_stds = [0.229, 0.224, 0.225]

    # Replace the first 3 channels with ImageNet BGR mean
    all_means[:3] = imagenet_bgr_mean

    # Extract standard deviation column, if available, else default to 1
    all_stds = data['std'].tolist()
    all_stds[:3] = imagenet_bgr_stds

    # Create and return the PyTorch normalization transform
    return transforms.Compose([
        #transforms.ToTensor(),  # Convert the image to a PyTorch tensor
        transforms.Normalize(mean=all_means, std=all_stds)  # Normalize using the modified means and stds
    ])


def preprocessing_sentinel2_TOA():
    """
    Sentinel-2 Top-of-Atmosphere reflectance normalization.
    All channels are scaled between 0 and 10000, no specific normalization used.
    """
    return transforms.Compose([
        #transforms.ToTensor(),  # Convert the image to a PyTorch tensor
        transforms.Normalize(mean=0, std=10000)  # Normalize by dividing by 10000 (range 0-10000)
    ])


def preprocessing_normalization_csv(csv_path):
    # Read the CSV into a pandas DataFrame
    data = pd.read_csv(csv_path)


    all_means = data['mean'].tolist()
    all_stds = data['std'].tolist()

    # Create and return the PyTorch normalization transform
    return transforms.Compose([
        #transforms.ToTensor(),  # Convert the image to a PyTorch tensor
        transforms.Normalize(mean=all_means, std=all_stds)  # Normalize using the modified means and stds
    ])




def get_preprocessing_pipeline(pretrained_weights, channels, normalization, normalization_path):
    if pretrained_weights == 'imagenet' and channels == 3:
        preprocessing = preprocessing_imagenet()
        print('preprocessing_imagenet')
    elif pretrained_weights == 'imagenet' and channels > 3 :
        assert normalization_path != None, "Normalization CSV must be computed to use imagenet for more then 3 channel to harmonize preprocessing."
        preprocessing = preprocessing_imagenet_additional(normalization_path)
        print('preprocessing_imagenet_more channels')
    elif pretrained_weights == 'Sentinel_2_TOA_Resnet18' or pretrained_weights == 'Sentinel_2_TOA_Resnet50':
        preprocessing = preprocessing_sentinel2_TOA()
        print('preprocessing_sentinel')# Sentinel-2 normalization for additional channels
    elif pretrained_weights is None and normalization == True and normalization_path != None:
        preprocessing = preprocessing_normalization_csv(normalization_path)
        print('preprocessing_normalization')
    else:
        preprocessing = None  # No preprocessing if conditions don't match

    return preprocessing








class CustomDataset(Dataset):
    """Reads in images, transforms pixel values, and serves a
    dictionary containing chip ids, image tensors, and
    label masks.
    """

    def __init__(
        self,
        csv_paths_dataframe:pd.DataFrame,
        transform: Optional[A.Compose] = None,
        num_classes: Optional[int] = None,
        preprocess_input: Optional= None,
        remove: Optional =None,
        scaler_loader: Optional =None,
            # Use A.Compose for transforms
    ):
        """

        Args:
            x_paths (pd.DataFrame): a dataframe with a row for each chip. There must be a column for chip_id,
                and a column with raster image, and a column with the corresponding mask.

            transforms (A.Compose, optional): Albumentations.Compose object for image augmentations.
        """
        self.data = csv_paths_dataframe
        # Remove the extra comma, and use the actual DataFrame
        self.transform = transform
        self.num_classes = num_classes
        self.preprocess_input = preprocess_input
        self.remove = remove
        self.scaler_loader = scaler_loader

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx: int):

        #id = self.data.loc[idx]
        img_path = self.data.loc[idx, 'image']  # Access the 'image' column
        mask_path = self.data.loc[idx, 'mask']   # Access the 'mask' column

        data = gdal.Open(img_path)

        ###
        mask = gdal.Open(mask_path)
        #channel first
        data_array = data.ReadAsArray().astype(np.float32)

        #if self.remove == True:
         #   mask_array = mask.ReadAsArray().astype(np.float32)
          #  mask = torch.as_tensor(mask_array, dtype=torch.int64)

            ######################### added ############################################################################################## what if no nodata class in dataset? make if condition!!!!!!
           # mask = mask.clamp(0, self.num_classes)
            #mask_array = torch.nn.functional.one_hot(mask,
            #                                         num_classes=self.num_classes + 1)  ## added +1 one to also encode no data class

            #mask_array = mask_array.permute(2, 0, 1).float()
            ###############################################################################################################################
            # remove one hot encoded first class ? how to adapt this for binary classes? ??
            #mask_array = mask_array[1:, :, :]
            #print(self.remove)
            #print(mask_array.shape)

        #else:
         #   mask_array = mask.ReadAsArray().astype(np.float32)
          #  mask = torch.as_tensor(mask_array, dtype=torch.int64) #-1  # to encode 1-3 to 0,1,2

           # mask = mask.clamp(0, self.num_classes)
            #mask_array = torch.nn.functional.one_hot(mask, num_classes=self.num_classes)
            #mask_array = mask_array.permute(2, 0, 1).float()
            #print(self.remove)
            #print(mask_array.shape)
        if self.num_classes == 1:
          mask_array = mask.ReadAsArray().astype(np.float32)
        # channel first
          mask_array = np.expand_dims(mask_array, axis=0)
        ############################################################################################################################ try
        elif self.remove == 'Yes':
          mask_array = mask.ReadAsArray().astype(np.float32)
          mask = torch.as_tensor(mask_array, dtype=torch.int64)

          ######################### added ############################################################################################## what if no nodata class in dataset? make if condition!!!!!!
          mask = mask.clamp(0, self.num_classes)
          mask_array = torch.nn.functional.one_hot(mask, num_classes=self.num_classes+1) ## added +1 one to also encode no data class

          mask_array = mask_array.permute(2, 0, 1).float()
          ###############################################################################################################################
          # remove one hot encoded first class ? how to adapt this for binary classes? ??
          mask_array = mask_array[1:, :, :]

        elif self.remove == 'No':
          mask_array = mask.ReadAsArray().astype(np.float32)
          mask = torch.as_tensor(mask_array, dtype=torch.int64)

          ######################### added ############################################################################################## what if no nodata class in dataset? make if condition!!!!!!
          mask = mask.clamp(0, self.num_classes-1)
          mask_array = torch.nn.functional.one_hot(mask, num_classes=self.num_classes) ## added +1 one to also encode no data class

          mask_array = mask_array.permute(2, 0, 1).float()
          ###############################################################################################################################
          # remove one hot encoded first class ? how to adapt this for binary classes? ??
          #mask_array = mask_array[1:, :, :]

        # Apply data augmentations, if provided

        if self.transform != None:
          mask_array = np.array(mask_array)
          data_array = np.array(data_array)
          #data_array = torch.as_tensor(data_array, dtype=torch.float32)
          #mask_array = torch.as_tensor(mask_array, dtype=torch.float32)

          data_array, mask_array = self.transform(data_array, mask_array)
          #data_array, mask_array = augmented['image'], augmented['mask']
        else:
          data_array = torch.as_tensor(data_array, dtype=torch.float32)
          mask_array = torch.as_tensor(mask_array, dtype=torch.float32)


        if self.scaler_loader != None:
            data_array /= self.scaler_loader

        if self.preprocess_input != None:

          data_array = torch.as_tensor(data_array, dtype=torch.float32)
          mask_array = torch.as_tensor(mask_array, dtype=torch.float32)
        # do preprcoessing for imagnet with this
          data_array = self.preprocess_input(data_array)
        # Convert back to channel first and then to tensors
          #data_array = np.transpose(data_array, (2, 0, 1))


        #print('preprocessed resnet18')

        #if self.scale != None:

        item = {'image':data_array,'mask':mask_array}
        return item

### Simple Model Unet
### source https://github.com/NTNU-SmallSat-Lab/s_l_c_segm_hyp_img/blob/main/Justoetal_models_public_released.py

class JustoUNetSimple(nn.Module):
    def __init__(self, input_channels, num_classes):
        super(JustoUNetSimple, self).__init__()
        # Encoder
        self.enc_conv1 = nn.Conv2d(input_channels, 6, kernel_size=3, padding=1)
        self.enc_bn1 = nn.BatchNorm2d(6)
        self.enc_conv2 = nn.Conv2d(6, 12, kernel_size=3, padding=1)
        self.enc_bn2 = nn.BatchNorm2d(12)

        # Decoder
        self.dec_conv1 = nn.Conv2d(12, 6, kernel_size=3, padding=1)
        self.dec_bn1 = nn.BatchNorm2d(6)
        self.dec_conv2 = nn.Conv2d(6, num_classes, kernel_size=3, padding=1)
        self.dec_bn2 = nn.BatchNorm2d(num_classes)

    def forward(self, x):
        # Encoder
        x = F.relu(self.enc_bn1(self.enc_conv1(x)))
        x = F.max_pool2d(x, 2)
        x = F.relu(self.enc_bn2(self.enc_conv2(x)))
        x = F.max_pool2d(x, 2)

        # Decoder
        x = F.interpolate(x, scale_factor=2, mode='nearest')
        x = F.relu(self.dec_bn1(self.dec_conv1(x)))
        x = F.interpolate(x, scale_factor=2, mode='nearest')
        x = self.dec_conv2(x)
        x = self.dec_bn2(x)
        return F.softmax(x, dim=1)

def model_2D_Justo_UNet_Simple(input_channels, num_classes):
    # Assuming input_size is (H, W, C)
    model = JustoUNetSimple(input_channels, num_classes)
    return model






class MyModel(L.LightningModule):
    def __init__(
        self,
        #bands: List[str],
        train_data: Optional[pd.DataFrame] = None,
        #y_train: Optional[pd.DataFrame] = None,
        val_data: Optional[pd.DataFrame] = None,
        #y_val: Optional[pd.DataFrame] = None,
        hparams: dict = None,
        feedback: QgsProcessingFeedback = None
    ):
        """

        Args:

            hparams (dict, optional): Dictionary of additional modeling parameters.
        """
        super().__init__()
        self.hparams.update(hparams)
        self.save_hyperparameters()

        # required
        #self.bands = bands

        # optional modeling params
        self.architecture = self.hparams.get("architecture", 'Unet') # Unet, Unet++, DeepLabV3+, MAnet
        self.backbone = self.hparams.get("backbone", 'resnet18') #resnet50
        self.weights = self.hparams.get("weights", None)#("weights", "imagenet")
        self.learning_rate = self.hparams.get("lr", None)
        self.num_workers = self.hparams.get("num_workers", 0)
        self.batch_size = self.hparams.get("batch_size", None)
        self.acc = self.hparams.get("acc", 'gpu')
        self.transform = self.hparams.get("transform",None) ##### changed after run test.
        self.in_channels =self.hparams.get("in_channels",None)
        self.classes = self.hparams.get("classes",None)
        #self.ignore_index = self.hparams.get("ignore_index",None)
        self.class_weights = self.hparams.get("class_weights", None)
        #self.loss_type =  self.hparams.get("loss", 'Balanced_MSE')
        self.checkpoint_path = self.hparams.get("checkpoint_path", None)
        self.freeze_encoder = self.hparams.get("freeze_backbone", False)
        self.img_x = self.hparams.get("img_x", None)
        self.img_y = self.hparams.get("img_y", None)
        self.preprocess=self.hparams.get("preprocess", None)
        self.counter = 0
        self.remove_b =self.hparams.get("remove_background_class", None)
        self.scaler =self.hparams.get("scaler", None)

        #self.feedback = feedback
        #added metrics
        # torch metrics log batch IoU
        #jaccard =
        #batch_iou = jaccard(preds, y)
        if self.classes == 1:
          #self.iou = JaccardIndex(task="binary",num_classes=self.classes, ignore_index=self.ignore_index)
          #self.val_iou = JaccardIndex(task="binary",num_classes=self.classes, ignore_index=self.ignore_index)
          self.iou = JaccardIndex(task="binary", num_classes=self.classes)
          self.val_iou = JaccardIndex(task="binary", num_classes=self.classes)
        else:
          #self.iou = JaccardIndex(task="multiclass",num_classes=self.classes, ignore_index=self.ignore_index)
          #self.val_iou = JaccardIndex(task="multiclass",num_classes=self.classes, ignore_index=self.ignore_index)
          self.iou = JaccardIndex(task="multiclass",num_classes=self.classes)
          self.val_iou = JaccardIndex(task="multiclass",num_classes=self.classes)

        # Instantiate datasets, model, and trainer params if provided


        self.train_dataset = CustomDataset(
            csv_paths_dataframe=train_data,
            transform=self.transform,
            num_classes=self.classes,#
            preprocess_input =self.preprocess,
            remove = self.remove_b,
            scaler_loader = self.scaler


        )


        self.val_dataset = CustomDataset(
            csv_paths_dataframe=val_data,
            transform=None,
            num_classes=self.classes,
            preprocess_input=self.preprocess,
            remove =self.remove_b,
            scaler_loader = self.scaler
            )



        self.model = self._prepare_model()


    def forward(self, image: torch.Tensor):
        # Forward pass
        return self.model(image)

    def training_step(self, batch: dict, batch_idx: int):
        """
        Training step.

        Args:

        """
        if self.train_dataset.data is None:
            raise ValueError(
                "Train Dataset must be specified to train model"
            )

        # Switch on training mode
        self.model.train()
        torch.set_grad_enabled(True)

        # Load images and labels


        x = batch["image"]
        y = batch["mask"]#.long()

        if self.acc == 'gpu':
            x, y = x.cuda(non_blocking=True), y.cuda(non_blocking=True)


        preds = self.forward(x)


        if self.classes == 1:
          train_loss = torch.nn.BCEWithLogitsLoss(weight = self.class_weights,reduction="mean")(preds, y)#.mean()
        else:
          train_loss = torch.nn.CrossEntropyLoss(weight = self.class_weights,reduction="mean")(preds, y)#.mean()


        # Log batch IOU
        preds = (preds > 0.5).int()
        train_iou = self.iou(preds, y)

        self.log_dict({'train_loss':train_loss,'train_iou':train_iou}
           , on_step=True, on_epoch=True, prog_bar=True, logger=True
        )

        return {'loss':train_loss,'train_iou':train_iou}

    def validation_step(self, batch: dict, batch_idx: int):
        """
        Validation step.

        Args:

        """
        if self.val_dataset.data is None:
            raise ValueError(
                "Validation Datset must be specified to train model"
            )

        # Switch on validation mode
        self.model.eval()
        torch.set_grad_enabled(False)

        # Load images and labels

        x = batch["image"]
        y = batch["mask"]#.long()
        if self.acc == 'gpu':
            x, y = x.cuda(non_blocking=True), y.cuda(non_blocking=True)


        preds = self(x)

        if self.classes == 1:
          val_loss = torch.nn.BCEWithLogitsLoss(weight = self.class_weights, reduction="mean")(preds, y)#.mean()
        else:
          val_loss = torch.nn.CrossEntropyLoss(weight = self.class_weights, reduction="mean")(preds, y)#.mean()

        preds = (preds > 0.5).int()
        val_iou = self.val_iou(preds, y)

        self.log_dict({'val_loss':val_loss,'val_iou':val_iou}
           , on_step=False, on_epoch=True, prog_bar=True, logger=True
        )

        return {'val_loss':val_loss,'val_iou':val_iou} #val_iou

    def predict(self, image: torch.Tensor):

        self.model.eval()
        torch.set_grad_enabled(False)

        if self.scaler != None:
            image /= self.scaler


        if self.preprocess != None:
            image = torch.as_tensor(image)

            image = self.preprocess(image)
        else:
            image = torch.as_tensor(image)

        logits = self(image)

        pred1 = torch.softmax(logits, dim=1)

        pred2 = torch.argmax(pred1, dim=1)  # Take the class with the highest probability


        #if self.remove_b == 'Yes':
         #   pred2 = pred2  + 1
            #### add here +1 for pred if background removed

        return pred2
    def train_dataloader(self):
        # DataLoader class for training
        return torch.utils.data.DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=True,
            pin_memory=True,
            drop_last=True
        )

    def val_dataloader(self):
        # DataLoader class for validation
        return torch.utils.data.DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
            pin_memory=True,
            drop_last=True
        )


    def configure_optimizers(self):
        opt = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=10)
        return [opt], [sch]

    def on_train_epoch_end(self):
        self.counter += 1  # Increment the counter
        self.log('counter', self.counter)

    def _prepare_model(self):


        ### weights selection and  backbone overwrite if miss match
        weights = None

        if self.architecture == 'Unet':
            model = smp.Unet(
                encoder_name=self.backbone,
                encoder_weights='imagenet' if self.weights == 'imagenet' else None,
                in_channels=self.in_channels,
                classes=self.classes
            )
        elif self.architecture == 'Unet++':
            model = smp.UnetPlusPlus(
                encoder_name=self.backbone,
                encoder_weights='imagenet' if self.weights == 'imagenet' else None,
                in_channels=self.in_channels,
                classes=self.classes
            )
        elif self.architecture == 'DeepLabV3+':
            model = smp.DeepLabV3Plus(
                encoder_name=self.backbone,
                encoder_weights='imagenet' if self.weights == 'imagenet' else None,
                in_channels=self.in_channels,
                classes=self.classes
            )
        elif self.architecture == 'MAnet':
            model = smp.MAnet(
                encoder_name=self.backbone,
                encoder_weights='imagenet' if self.weights == 'imagenet' else None,
                in_channels=self.in_channels,
                classes=self.classes
            )
        elif self.architecture == 'JustoUNetSimple':

            model = model_2D_Justo_UNet_Simple(input_channels=self.in_channels, num_classes=self.classes)

        # loader for backbone

        #if self.weights != 'imagenet' or self.weights != None:
        if self.weights not in ['imagenet', None]:
            try:
                if isinstance(self.weights, str):
                    if self.weights == 'Sentinel_2_TOA_Resnet18':

                        assert self.in_channels == 13, f'Input channels should be equal to 13 , but is {self.in_channels}'
                        weights = ResNet18_Weights.SENTINEL2_ALL_MOCO
                        self.backbone = 'resnet18'

                    elif self.weights == 'Sentinel_2_TOA_Resnet50':
                        assert self.in_channels == 13, f'Input channels should be equal to 13 , but is {self.in_channels}'
                        weights = ResNet50_Weights.SENTINEL2_ALL_MOCO
                        self.backbone = 'resnet50'

                    #elif self.weights == 'LANDSAT_TM_TOA_Resnet18':
                     #   assert self.in_channels == 7, f'Input channels should be equal to 7 , but is {self.in_channels}'
                      #  weights = ResNet18_Weights.LANDSAT_TM_TOA_MOCO
                       # self.backbone = 'resnet18'

                    #elif self.weights == 'LANDSAT_ETM_TOA_Resnet18':
                     #   assert self.in_channels ==  9, f'Input channels should be equal to 9 , but is {self.in_channels}'
                      #  weights = ResNet18_Weights.LANDSAT_ETM_TOA_MOCO
                       # self.backbone = 'resnet18'

                    #elif self.weights == 'LANDSAT_OLI_TIRS_TOA_Resnet18':
                     #   assert self.in_channels == 11, f'Input channels should be equal to 11 , but is {self.in_channels}'
                      #  weights = ResNet18_Weights.LANDSAT_OLI_TIRS_TOA_MOCO
                       # self.backbone = 'resnet18'

                    #elif self.weights == 'LANDSAT_ETM_SR_Resnet18':
                     #   assert self.in_channels == 6, f'Input channels should be equal to 6 , but is {self.in_channels}'
                      #  weights = ResNet18_Weights.LANDSAT_ETM_SR_MOC
                       # self.backbone = 'resnet18'

                    #elif self.weights == 'LANDSAT_OLI_SR_Resnet18':
                     #   assert self.in_channels == 7, f'Input channels should be equal to 7 , but is {self.in_channels}'
                      #  weights = ResNet18_Weights.LANDSAT_OLI_SR_MOCO
                       # self.backbone = 'resnet18'

                    # Load custom weights via weights enum
                weight_enum = get_weight(self.weights)
                if weight_enum is not None:
                    state_dict = weight_enum.get_state_dict(progress=True)
                    model.encoder.load_state_dict(state_dict)

            except Exception as e:
                print(f"Warning: Failed to load custom weights: {str(e)}")

        if self.freeze_encoder == True:
                # Freeze encoder weights
                for param in model.encoder.parameters():
                    param.requires_grad = False


        return model


class FeedbackCallback(L.Callback):
    def __init__(self, feedback):
        super().__init__()
        self.feedback = feedback

    def on_batch_end(self, trainer, pl_module):
        # Check for cancellation after every batch
        if self.feedback and self.feedback.isCanceled():
            raise KeyboardInterrupt("Training canceled by user.")
    def on_train_epoch_end(self, trainer, pl_module):
        epoch = trainer.current_epoch
        max_epochs = trainer.max_epochs

        train_loss = trainer.callback_metrics.get('train_loss')
        train_iou = trainer.callback_metrics.get('train_iou')
        val_loss = trainer.callback_metrics.get('val_loss')
        val_iou = trainer.callback_metrics.get('val_iou')

        log_message = (
            f'Epoch {epoch + 1}/{max_epochs} - '
            f'Train Loss: {train_loss:.4f}, Train IoU: {train_iou:.4f}, '
            f'Val Loss: {val_loss:.4f}, Val IoU: {val_iou:.4f}'
        )

        if self.feedback:
            self.feedback.setProgress((epoch + 1) / max_epochs * 100)
            self.feedback.pushInfo(log_message)
            # Allow user to cancel the process
            # Check if the user canceled the process
            if self.feedback.isCanceled():
                trainer.should_stop = True
                self.feedback.pushInfo('Training canceled by user')
                raise KeyboardInterrupt("Training canceled by user.")


        print(log_message)




def dl_train(#train_data_csv,
             # val_data_csv,
             input_folder,
             arch_index, backbone='resnet18', pretrained_weights_index=0,
             #n_classes=20,
             checkpoint_path=None,
             freeze_encoder=True, data_aug=True, batch_size=16, n_epochs=100, lr=0.0001, early_stop=True,
             #ignore_index=None,
             class_weights_balanced=True,
             normalization_bool =True,
             num_workers=0, num_models =1, acc_type_index=None, acc_type_numbers=1,logdirpath_model=None, logdirpath='./logs',tune =True,feedback:QgsProcessingFeedback=None):

    arch_index_options = ['Unet', 'Unet++','DeepLabV3+','MAnet','JustoUNetSimple']
    arch = arch_index_options[arch_index]

    pretrained_weights_options = ['imagenet', None, 'Sentinel_2_TOA_Resnet18','Sentinel_2_TOA_Resnet50']#,'LANDSAT_TM_TOA_Resnet18','LANDSAT_ETM_TOA_Resnet18','LANDSAT_OLI_TIRS_TOA_Resnet18','LANDSAT_ETM_SR_Resnet18','LANDSAT_OLI_SR_Resnet18']
    pretrained_weights = pretrained_weights_options[pretrained_weights_index]

    if arch == 'JustoUNetSimple':
        freeze_encoder = False

    #### load data

    def fix_path(path):
        return path.replace('\\', '/')

    # Make sure the folder path uses forward slashes
    folder_path = fix_path(input_folder)

    train_data_path = folder_path + '/train_files.csv'
    val_data_path = folder_path + '/validation_files.csv'
    summary_data_path = folder_path + '/Summary_train_val.csv'



    train_data = pd.read_csv(train_data_path)
    val_data = pd.read_csv(val_data_path)
    summary_data = pd.read_csv(summary_data_path)

            # Extract the 'weights' column as a list
    n_classes = len(summary_data['Class ID'].tolist())

    ###################### read from csv
    remove_zero_class = summary_data['Ignored Background : Class Zero'].tolist()[0]
    print( 'remove zero class', remove_zero_class )
    scaler_list = summary_data['Scaler'].tolist()
    scaler = scaler_list[0]
    print('scaler',scaler)
    print(f"Initial scaler: {scaler} (type: {type(scaler)})")

    ignore_scaler_list = ([
        'Sentinel_2_TOA_Resnet18', 'Sentinel_2_TOA_Resnet50'])

     #   ,'LANDSAT_TM_TOA_Resnet18', 'LANDSAT_ETM_TOA_Resnet18','LANDSAT_OLI_TIRS_TOA_Resnet18', 'LANDSAT_ETM_SR_Resnet18', 'LANDSAT_OLI_SR_Resnet18'])

    scaler_value = None if pretrained_weights in ignore_scaler_list else summary_data['Scaler'].iloc[0]

    # Handle NaN values
    if isinstance(scaler_value, float) and math.isnan(scaler_value):
        scaler_value = None

    print(f"Scaler after handling NaN: {scaler} (type: {type(scaler)})")

    ### data aug:
    if data_aug == True:
        # Assuming transform setup here
        transform = v2.Compose([
            v2.RandomRotation(degrees=45),
            v2.RandomHorizontalFlip(p=0.5),
            v2.RandomVerticalFlip(p=0.5),
        ])
    else:
        transform = None

    acc_type_options = ['cpu', 'gpu']
    acc_type = acc_type_options[acc_type_index]

    #### balanced training
    if class_weights_balanced == True:

            # Extract the 'weights' column as a list
        weights_list = summary_data['Class Train Weight'].tolist()

        if acc_type == 'gpu':
            weights_tensor = torch.as_tensor(weights_list, dtype=torch.float32).cuda()

        elif acc_type == 'cpu':
            weights_tensor = torch.as_tensor(weights_list, dtype=torch.float32)
    else:
        weights_tensor = None

    # Load the first image and mask to determine their dimensions
    first_image_path = train_data['image'].iloc[0]
    first_img = gdal.Open(first_image_path, gdal.GA_ReadOnly)
    in_channels = first_img.RasterCount
    first_img_x = first_img.RasterXSize
    first_img_y = first_img.RasterYSize

    if arch =='JustoUNetSimple':
        backbone = None


    # initalize preprocessing in regards to normalization or pretrained weights
    if normalization_bool == True:
        normalize_data_path = folder_path + '/Normalize_Bands.csv'
        preprocess_input = get_preprocessing_pipeline(pretrained_weights, channels= in_channels, normalization= normalization_bool, normalization_path =normalize_data_path)
    else:
        preprocess_input = get_preprocessing_pipeline(pretrained_weights, channels=in_channels,
                                                      normalization=None,
                                                      normalization_path=None)



    model = MyModel(
        train_data=train_data,
        val_data=val_data,
        hparams={
            'in_channels': in_channels,
            'architecture': arch,
            'classes': n_classes,
            'batch_size': batch_size,
            'backbone': backbone,
            'weights': pretrained_weights,
            'epochs': n_epochs,
            'transform': transform,
            'lr': lr,
            'num_workers': num_workers,
            'acc': acc_type,
            'freeze_backbone': freeze_encoder,
            #"ignore_index": ignore_index,
            "class_weights": weights_tensor,
            'checkpoint_path': None,
            "img_x":first_img_x,
            "img_y":first_img_y,
            "preprocess":preprocess_input,
            "remove_background_class" : remove_zero_class,
            "scaler": scaler_value
        }
        #feedback = feedback
    )

    if checkpoint_path ==True :
        print('loaded from checkpoint')
        model = MyModel.load_from_checkpoint(checkpoint_path, train_data=train_data, val_data=val_data,
                                             hparams={'in_channels': in_channels,
            'architecture': arch,### take out as shoul have been devined already
            'classes': n_classes, ### take out as shoul have been devined already
            'batch_size': batch_size,
            'backbone': backbone, ### take out as shoul have been devined already
            'weights': pretrained_weights,
            'epochs': n_epochs,
            'transform': transform,
            'lr': lr,
            'num_workers': num_workers,
            'acc': acc_type,
            'freeze_backbone': freeze_encoder,
            #"ignore_index": ignore_index,
            "class_weights": weights_tensor,
            'checkpoint_path': None,
            "img_x":first_img_x,
            "img_y":first_img_y,
            "preprocess":preprocess_input,
            "remove_background_class" : remove_zero_class,
            "scaler": scaler_value                                          },
            map_location=acc_type
        )

    # Callbacks
    if early_stop == True:
        early_stopping_callback = EarlyStopping("val_iou", mode="max", verbose=True, patience=20)

        checkpoint_callback = ModelCheckpoint(dirpath=logdirpath_model, monitor='val_iou', #,monitor='val_iou_epoch'
                                              filename='{epoch:02d}-{val_iou_epoch:.2f}', save_top_k=num_models,
                                              auto_insert_metric_name=False)

        feedback_callback = FeedbackCallback(feedback=feedback)

        logger = TensorBoardLogger(save_dir=logdirpath, name="lightning_logs")
        trainer = L.Trainer(
            max_epochs=n_epochs,
            accelerator=acc_type,
            devices=acc_type_numbers,
            logger=logger,
            log_every_n_steps= 1,
            callbacks=[checkpoint_callback, early_stopping_callback,feedback_callback]
        )



        if tune == True:
            tuner = Tuner(trainer)

            # Run learning rate finder
            lr_finder = tuner.lr_find(model)

            # Results can be found in
            print('lr', lr_finder.results)

            new_lr = lr_finder.suggestion()
            # update hparams of the model
            model.hparams.lr = new_lr


        trainer.fit(model)

    else:
        checkpoint_callback = ModelCheckpoint(dirpath=logdirpath, monitor='val_iou',  # ,monitor='val_iou_epoch'
                                              filename='{epoch:02d}-{val_iou_epoch:.2f}', save_top_k=num_models,
                                              auto_insert_metric_name=False)

        feedback_callback = FeedbackCallback(feedback=feedback)

        logdir = logdirpath
        logger = TensorBoardLogger(save_dir=logdir, name="lightning_logs")
        trainer = L.Trainer(
            max_epochs=n_epochs,
            accelerator=acc_type,
            devices=acc_type_numbers,
            logger=logger,
            log_every_n_steps=1,
            callbacks=[checkpoint_callback, feedback_callback]

        )



        if tune == True:
            tuner = Tuner(trainer)

            # Run learning rate finder
            lr_finder = tuner.lr_find(model)

            # Results can be found in
            print('lr', lr_finder.results)

            new_lr = lr_finder.suggestion()
            # update hparams of the model
            model.hparams.lr = new_lr

        trainer.fit(model)


    return