# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Pre-trained ResNet models."""

from typing import Any

#import kornia.augmentation as K
import timm
import torch
from timm.models import ResNet
from torchvision.models._api import Weights, WeightsEnum




# https://github.com/zhu-xlab/SSL4EO-S12/blob/d2868adfada65e40910bfcedfc49bc3b20df2248/src/benchmark/transfer_classification/linear_BE_moco.py#L167
# https://github.com/zhu-xlab/SSL4EO-S12/blob/d2868adfada65e40910bfcedfc49bc3b20df2248/src/benchmark/transfer_classification/datasets/EuroSat/eurosat_dataset.py#L97
# Normalization either by 10K (for S2 uint16 input) or channel-wise with band statistics
#_ssl4eo_s12_transforms_s2_10k = K.AugmentationSequential(
 #   K.Resize(256),
  #  K.CenterCrop(224),
   # K.Normalize(mean=torch.tensor(0), std=torch.tensor(10000)),
    #data_keys=None,
#)





# https://github.com/microsoft/torchgeo/blob/8b53304d42c269f9001cb4e861a126dc4b462606/torchgeo/datamodules/ssl4eo_benchmark.py#L43
#_ssl4eo_l_transforms = K.AugmentationSequential(
 #   K.Normalize(mean=torch.tensor(0), std=torch.tensor(255)),
  #  K.CenterCrop((224, 224)),
   # data_keys=None,
#)
from typing import Optional, Any

from torchvision.transforms import v2


# Transform for S2 10K normalized images
_ssl4eo_s12_transforms_s2_10k = v2.Compose([
    v2.Resize(256),  # Resize to 256x256
    #transforms.CenterCrop(224),  # Center crop to 224x224
    #transforms.ToTensor(),  # Convert image to PyTorch tensor
    v2.Normalize(mean=(0,), std=(10000,))  # Normalize by 10,000 for S2 uint16 input
])

# Transform for 8-bit Landsat images normalized by 255
_ssl4eo_l_transforms = v2.Compose([
    #transforms.ToTensor(),  # Convert image to PyTorch tensor
    v2.Normalize(mean=(0,), std=(255,)),  # Normalize by 255 for 8-bit uint8 input
    #transforms.CenterCrop(224)  # Center crop to 224x224
])
# https://github.com/pytorch/vision/pull/6883
# https://github.com/pytorch/vision/pull/7107
# Can be removed once torchvision>=0.15 is required
Weights.__deepcopy__ = lambda *args, **kwargs: args[0]


class ResNet18_Weights(WeightsEnum):  # type: ignore[misc]
    """ResNet-18 weights.

    For `timm <https://github.com/huggingface/pytorch-image-models>`_
    *resnet18* implementation.

    .. versionadded:: 0.4
    """

    LANDSAT_TM_TOA_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet18_landsat_tm_toa_moco-1c691b4f.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 7,
            'model': 'resnet18',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )



    LANDSAT_ETM_TOA_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet18_landsat_etm_toa_moco-bb88689c.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 9,
            'model': 'resnet18',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )

    LANDSAT_OLI_TIRS_TOA_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet18_landsat_oli_tirs_toa_moco-a3002f51.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 11,
            'model': 'resnet18',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )

    LANDSAT_ETM_SR_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet18_landsat_etm_sr_moco-4f078acd.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 6,
            'model': 'resnet18',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )


    LANDSAT_OLI_SR_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet18_landsat_oli_sr_moco-660e82ed.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 7,
            'model': 'resnet18',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },

    )


    SENTINEL2_ALL_MOCO = Weights(
        url='https://hf.co/torchgeo/resnet18_sentinel2_all_moco/resolve/5b8cddc9a14f3844350b7f40b85bcd32aed75918/resnet18_sentinel2_all_moco-59bfdff9.pth',
        transforms=_ssl4eo_s12_transforms_s2_10k,
        meta={
            'dataset': 'SSL4EO-S12',
            'in_chans': 13,
            'model': 'resnet18',
            'publication': 'https://arxiv.org/abs/2211.07044',
            'repo': 'https://github.com/zhu-xlab/SSL4EO-S12',
            'ssl_method': 'moco',
        },
    )





class ResNet50_Weights(WeightsEnum):  # type: ignore[misc]
    """ResNet-50 weights.

    For `timm <https://github.com/huggingface/pytorch-image-models>`_
    *resnet50* implementation.

    .. versionadded:: 0.4
    """


    LANDSAT_TM_TOA_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet50_landsat_tm_toa_moco-ba1ce753.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 7,
            'model': 'resnet50',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )



    LANDSAT_ETM_TOA_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet50_landsat_etm_toa_moco-e9a84d5a.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 9,
            'model': 'resnet50',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )


    LANDSAT_ETM_SR_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet50_landsat_etm_sr_moco-1266cde3.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 6,
            'model': 'resnet18',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )


    LANDSAT_OLI_TIRS_TOA_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet50_landsat_oli_tirs_toa_moco-de7f5e0f.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 11,
            'model': 'resnet50',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )


    LANDSAT_OLI_SR_MOCO = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet50_landsat_oli_sr_moco-ff580dad.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 7,
            'model': 'resnet50',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'moco',
        },
    )

    LANDSAT_OLI_SR_SIMCLR = Weights(
        url='https://hf.co/torchgeo/ssl4eo_landsat/resolve/1c88bb51b6e17a21dde5230738fa38b74bd74f76/resnet50_landsat_oli_sr_simclr-94f78913.pth',
        transforms=_ssl4eo_l_transforms,
        meta={
            'dataset': 'SSL4EO-L',
            'in_chans': 7,
            'model': 'resnet50',
            'publication': 'https://arxiv.org/abs/2306.09424',
            'repo': 'https://github.com/microsoft/torchgeo',
            'ssl_method': 'simclr',
        },
    )

    SENTINEL2_ALL_MOCO = Weights(
        url='https://hf.co/torchgeo/resnet50_sentinel2_all_moco/resolve/da4f3c9dbe09272eb902f3b37f46635fa4726879/resnet50_sentinel2_all_moco-df8b932e.pth',
        transforms=_ssl4eo_s12_transforms_s2_10k,
        meta={
            'dataset': 'SSL4EO-S12',
            'in_chans': 13,
            'model': 'resnet50',
            'publication': 'https://arxiv.org/abs/2211.07044',
            'repo': 'https://github.com/zhu-xlab/SSL4EO-S12',
            'ssl_method': 'moco',
        },
    )
###################################################################################################################
# for python 3.10 +  def resnet18(
 #   weights: ResNet18_Weights | None = None, *args: Any, **kwargs: Any
#) -> ResNet

def resnet50(
            weights: Optional[ResNet50_Weights] = None, *args: Any, **kwargs: Any
    ) -> ResNet:
    """ResNet-18 model.

    If you use this model in your research, please cite the following paper:

    * https://arxiv.org/pdf/1512.03385

    .. versionadded:: 0.4

    Args:
        weights: Pre-trained model weights to use.
        *args: Additional arguments to pass to :func:`timm.create_model`
        **kwargs: Additional keywork arguments to pass to :func:`timm.create_model`

    Returns:
        A ResNet-18 model.
    """
    if weights:
        kwargs['in_chans'] = weights.meta['in_chans']

    model: ResNet = timm.create_model('resnet18', *args, **kwargs)

    if weights:
        missing_keys, unexpected_keys = model.load_state_dict(
            weights.get_state_dict(progress=True), strict=False
        )
        assert set(missing_keys) <= {'fc.weight', 'fc.bias'}
        assert not unexpected_keys

    return model


#  for python 3.10 + def resnet50(
 #   weights: ResNet50_Weights | None = None, *args: Any, **kwargs: Any
#) -> ResNet:
def resnet50(
            weights: Optional[ResNet50_Weights] = None, *args: Any, **kwargs: Any
    ) -> ResNet:
    """ResNet-50 model.

    If you use this model in your research, please cite the following paper:

    * https://arxiv.org/pdf/1512.03385

    .. versionchanged:: 0.4
       Switched to multi-weight support API.

    Args:
        weights: Pre-trained model weights to use.
        *args: Additional arguments to pass to :func:`timm.create_model`.
        **kwargs: Additional keywork arguments to pass to :func:`timm.create_model`.

    Returns:
        A ResNet-50 model.
    """
    if weights:
        kwargs['in_chans'] = weights.meta['in_chans']

    model: ResNet = timm.create_model('resnet50', *args, **kwargs)

    if weights:
        missing_keys, unexpected_keys = model.load_state_dict(
            weights.get_state_dict(progress=True), strict=False
        )
        assert set(missing_keys) <= {'fc.weight', 'fc.bias'}
        assert not unexpected_keys

    return model

