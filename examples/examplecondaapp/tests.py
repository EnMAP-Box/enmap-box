# coding=utf-8

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'

import unittest
import os
from enmapbox.testing import initQgisApplication
from examplecondaapp.exampleapp import AnacondaEnvironmentInfo

QGIS_APP = initQgisApplication()

ANACONDA_ROOT = r'C:\Users\geo_beja\AppData\Local\Continuum\miniconda3'
assert os.path.isdir(ANACONDA_ROOT), 'This test requires to specify a local Anaconda Environment'


class AnacondaEnvironmentInfoTests(unittest.TestCase):

    def test_initialisation(self):
        self.assertTrue(AnacondaEnvironmentInfo.isAnacondaEnvironment(ANACONDA_ROOT))
        AI = AnacondaEnvironmentInfo(ANACONDA_ROOT)
        self.assertTrue(AI.isValid())

        self.assertTrue(os.path.isdir(AI.scriptFolder()))
        self.assertTrue(os.path.isfile(AI.pythonExecutable()))
        self.assertTrue(os.path.isfile(AI.activateScript()))


if __name__ == "__main__":
    unittest.main()
