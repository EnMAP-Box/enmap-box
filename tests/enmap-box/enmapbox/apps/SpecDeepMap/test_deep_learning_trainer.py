import glob
import os
import re
import unittest
from pathlib import Path

from enmapbox import DIR_UNITTESTS
from enmapbox.apps.SpecDeepMap import import_error
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from processing import Processing

if import_error is None:
    try:
        import lightning

        print(lightning)
    except Exception as error:
        import_error = error

if not import_error:
    import lightning as L
    import torch
    from torchvision import transforms
    from torchvision.transforms import v2
    from enmapbox.apps.SpecDeepMap import DL_Trainer
    from enmapbox.apps.SpecDeepMap.core_deep_learning_trainer import MyModel

    start_app()

BASE_TESTDATA = Path(DIR_UNITTESTS) / 'testdata/external/specdeepmap'


def best_ckpt_path(checkpoint_dir):
    pattern = re.compile(r'val_iou_(\d+\.\d{4})')
    return max(
        (os.path.join(checkpoint_dir, f) for f in os.listdir(checkpoint_dir) if pattern.search(f)),
        key=lambda f: float(pattern.search(f).group(1))
    )


@unittest.skipIf(import_error, f'Missing modules to run SpecDeepMap: {import_error}')
class Test_Deep_Learning_Trainer(TestCase):

    def test_Justo_simple_unet(self):

        # run algorithm
        alg = DL_Trainer()

        # Get the script's directory (makes paths relative)
        # BASE_DIR = Path(__file__).parent
        # BASE_DIR = self.createTestOutputDirectory()
        folder_path_input = BASE_TESTDATA / 'test_requierments'
        self.assertTrue(folder_path_input.is_dir())
        # folder_path = BASE_DIR / "test_run"
        folder_path = self.createTestOutputDirectory()
        self.assertTrue(folder_path.is_dir(), msg=f'Dir does not exists: {folder_path}')

        folder_path = folder_path.as_posix()
        folder_path_input = folder_path_input.as_posix()

        # delete checkpoint files from previous test
        for filename in os.listdir(folder_path):
            if filename.endswith(".ckpt"):  # Assuming checkpoint files have a .ckpt extension
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)

        io = {alg.train_val_input_folder: folder_path_input,
              alg.arch: 4,
              alg.backbone: 'resnet18',
              alg.pretrained_weights: 1,
              alg.freeze_encoder: False,
              alg.data_aug: True,
              alg.batch_size: 2,
              alg.n_epochs: 2,
              alg.lr: 0.001,
              alg.lr_finder: False,
              alg.pat: True,
              alg.class_weights_balanced: True,
              alg.normalization_flag: True,
              alg.device: 0,
              alg.num_workers: 0,
              alg.device_numbers: 1,
              alg.num_models: -1,
              alg.tensorboard: False,
              alg.logdirpath: folder_path,
              alg.logdirpath_model: folder_path,
              }

        result = Processing.runAlgorithm(alg, parameters=io)

        print(result)

        # 1. Test saved models as amount of epochs (2)
        ckpt_file = glob.glob(f"{folder_path}/*.ckpt")
        ckpt_len = len(ckpt_file)  # List all .tif files
        assert ckpt_len == 2, "Error: Expected 2 saved checkpoints, as 2 epochs were trained with every epoch saving"

        # test model load:

        # select best ckpt
        best = best_ckpt_path(folder_path)

        model_loaded = MyModel.load_from_checkpoint(best)

        # 2. Test check if model has subclass, pytorch lightning Module
        is_inherited = isinstance(model_loaded, L.LightningModule)
        assert is_inherited is True, "Model did not inherit Lightning Module"

        # 3. Test: check if hparams used in training have been passed correctly to class and checkpoint saver

        print(model_loaded.hparams)
        assert 0.001 == model_loaded.hparams.lr, 'learning rate not passed correctly'
        assert 'JustoUNetSimple' == model_loaded.hparams.architecture, 'Model architecture not passed correctly'
        assert isinstance(model_loaded.hparams.class_weights,
                          torch.Tensor), f"class_weights is not a torch.Tensor, it is {type(model_loaded.hparams.class_weights)}"
        assert isinstance(model_loaded.hparams.transform,
                          v2.Compose), f'Data augmentation should be torchvision Compose, but is , it is {type(model_loaded.hparams.transform)}'
        assert isinstance(model_loaded.hparams.preprocess,
                          transforms.Compose), f'Preprocess should be torchvision Compose, but is , it is {type(model_loaded.hparams.preprocess)}'

        # delete checkpoint files from previous test
        for filename in os.listdir(folder_path):
            if filename.endswith(".ckpt"):  # Assuming checkpoint files have a .ckpt extension
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)

    def test_unet_resnet_api(self):

        # run algorithm
        alg = DL_Trainer()

        # Get the script's directory (makes paths relative)
        # BASE_DIR = dirname(__file__)
        # folder_path = join(BASE_DIR, "test_run")
        folder_path = self.createTestOutputDirectory()
        folder_path_input = BASE_TESTDATA / 'test_requierments'

        # 4. Test check if pretrained model runs needs 13 channel adjust indexing before splitting raster
        io = {alg.train_val_input_folder: folder_path_input.as_posix(),
              alg.arch: 0,
              alg.backbone: 'resnet18',
              alg.pretrained_weights: 0,
              alg.freeze_encoder: True,
              alg.data_aug: True,
              alg.batch_size: 2,
              alg.n_epochs: 2,
              alg.lr: 0.003,
              alg.lr_finder: False,
              alg.pat: True,
              alg.class_weights_balanced: True,
              alg.normalization_flag: True,
              alg.device: 0,
              alg.num_workers: 0,
              alg.device_numbers: 1,
              alg.num_models: -1,
              alg.tensorboard: False,
              alg.logdirpath: folder_path.as_posix(),
              alg.logdirpath_model: folder_path.as_posix(),
              }

        result = Processing.runAlgorithm(alg, parameters=io)

        best = best_ckpt_path(folder_path)

        model_loaded = MyModel.load_from_checkpoint(best)

        # 2. Test check if model has subclass, pytorch lightning Module
        is_inherited = isinstance(model_loaded, L.LightningModule)
        assert is_inherited is True, "Model did not inherite Lightning Module"

        # 3. Test: check if hparams used in training have been passed correctly to class and checkpoint saver

        print(model_loaded.hparams)

        assert 'Unet' == model_loaded.hparams.architecture, 'Model architecture not passed correctly'
        assert 'resnet18' == model_loaded.hparams.backbone, 'Model backbone not passed correctly'
        assert 'imagenet' == model_loaded.hparams.weights, 'Model backbone not passed correctly'
        # assert all(not param.requires_grad for param in model_loaded.backbone.parameters()), "Error: The model's backbone is not frozen."

        # actual_backbone = getattr(model_loaded, 'backbone', None)  # Replace 'backbone_model' if needed
        # assert actual_backbone is not None, "Backbone model not found"

        # Check if backbone is frozen
        # frozen = all(not param.requires_grad for param in actual_backbone.parameters())
        # assert frozen, "Error: The model's backbone is not frozen."

        # delete checkpoint files from previous test
        for filename in os.listdir(folder_path):
            if filename.endswith(".ckpt"):  # Assuming checkpoint files have a .ckpt extension
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)
