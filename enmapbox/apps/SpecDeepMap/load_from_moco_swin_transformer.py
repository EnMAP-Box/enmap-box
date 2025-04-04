import re
from collections import OrderedDict

import torch

path = "C:/test_cursor/version_19_10epoch_10and50m_mocov3_swintiny/checkpoints/epoch=8-step=2925.ckpt"
checkpoint = torch.load(path, map_location=torch.device('cpu'))
print(checkpoint['hyper_parameters'])

state_dict_mod = checkpoint['state_dict']
print("Keys in state dict modified:", state_dict_mod.keys())
# Get only the backbone keys (not backbone_momentum)
state_dict_mod = OrderedDict(
    {k: v for k, v in state_dict_mod.items() if k.startswith('backbone.') and not k.startswith('backbone_momentum')})
# Remove the 'backbone.' prefix to match the target model's keys
state_dict_mod = OrderedDict(
    {k.replace('backbone.', 'model.'): v for k, v in state_dict_mod.items()}
)

state_dict_mod = {re.sub(r'(?<=layers).', '_', k): v for k, v in state_dict_mod.items()}

print("Keys in state dict modified:", state_dict_mod.keys())
# load whole model with weights
ignore_keys = {"model.norm.weight", "model.norm.bias"}

# Filter out unwanted keys
state_dict_mod = {k: v for k, v in state_dict_mod.items() if k not in ignore_keys}

import segmentation_models_pytorch as smp

model = smp.Unet(
    encoder_name='tu-swin_s3_tiny_224',
    encoder_weights=None,
    in_channels=7,
    classes=10
)

print("Keys expected by model:", model.encoder.state_dict().keys())
#

model.encoder.load_state_dict(state_dict_mod)

#############


import torch

# print(checkpoint['weights'])
# print('state_dict', state_dict)
# Print the keys from your loaded state dict
# print("Keys in loaded state dict:", state_dict.keys())

# Print the keys expected by the model


# this is from torchgeo moco task trained a renset 18

# path = "C:/test_cursor/version_3_50m_only/checkpoints/epoch=199-step=17600.ckpt"
# checkpoint = torch.load(path, map_location=torch.device('cpu'))

# state_dict_mod = checkpoint['state_dict']
# Get only the backbone keys (not backbone_momentum)
# state_dict_mod = OrderedDict(
#   {k: v for k, v in state_dict_mod.items() if k.startswith('backbone.') and not k.startswith('backbone_momentum')})
# Remove the 'backbone.' prefix to match the target model's keys
# state_dict_mod = OrderedDict(
#   {k.replace('backbone.', ''): v for k, v in state_dict_mod.items()}
# )

print("Keys in state dict modified:", state_dict_mod.keys())
# load whole model with weights


import segmentation_models_pytorch as smp

model = smp.Unet(
    encoder_name='tu-swin_s3_tiny_224',
    encoder_weights=None,
    in_channels=7,
    classes=10
)

print("Keys expected by model:", model.encoder.state_dict().keys())
#

# Save initial weights for comparison
initial_weights = OrderedDict(model.encoder.state_dict())

# Load the new weights
model.encoder.load_state_dict(state_dict_mod)

# Compare weights
print("\nVerifying weights loading:")
for key in model.encoder.state_dict().keys():
    if key in state_dict_mod:
        loaded_tensor = model.encoder.state_dict()[key]
        source_tensor = state_dict_mod[key]

        # Check if tensors are exactly equal
        if torch.equal(loaded_tensor, source_tensor):
            print(f"✓ {key}: Weights match exactly")
        else:
            # If not equal, print some statistics
            print(f"✗ {key}: Weights differ!")
            print(f"  Max difference: {torch.max(torch.abs(loaded_tensor - source_tensor))}")
            print(f"  Mean difference: {torch.mean(torch.abs(loaded_tensor - source_tensor))}")
    else:
        print(f"! {key}: Key not found in source weights")

# Print shape comparison for first layer as sanity check
