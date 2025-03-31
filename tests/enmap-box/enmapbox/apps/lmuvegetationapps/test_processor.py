import os
import unittest
from pathlib import Path

from qgis.core import QgsApplication
from enmapboxprocessing.testcase import TestCase
from lmuvegetationapps.Processor.Processor_Training_GUI import MainUiFunc, ML_Training, MLTrainingGUI

DIR_TESTDATA = Path(__file__).parent / 'data'


class LMUTests_Processor(TestCase):

    @unittest.skipIf(TestCase.runsInCI(), 'Takes too long. Local test only.')
    def test_processor_training(self):
        path_lut = DIR_TESTDATA / 'TestLUT_2000_CpCBCcheck_00meta.lut'

        dir_outputs = self.createTestOutputDirectory()
        os.makedirs(dir_outputs, exist_ok=True)

        main = MainUiFunc()
        training: ML_Training = main.mlra_training
        gui: MLTrainingGUI = training.gui

        # set parameters in GUI
        training.open_lut(path=str(path_lut))
        training.gui.radNoiseOff.click()
        training.gui.chkAGBdry.setChecked(True)
        training.gui.rbGPR.click()
        training.gui.radAL.click()
        training.gui.txtTrainSize.setText('50')

        training.gui.txtModelDir.setText(dir_outputs.as_posix())
        training.out_dir = training.gui.txtModelDir.text()
        training.gui.txtModelName.setText("test")
        training.model_name = training.gui.txtModelName.text()

        training.gui.show()
        if False:
            training.run_training()
        self.showGui(gui)
        QgsApplication.exec_()
