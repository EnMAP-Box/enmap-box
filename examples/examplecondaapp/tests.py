# coding=utf-8

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'

import unittest
from qgis import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from enmapbox.testing import initQgisApplication
QGIS_APP = initQgisApplication()

ANACONDA_ROOT = r'C:\Users\geo_beja\AppData\Local\Continuum\miniconda3'
assert os.path.isdir(ANACONDA_ROOT), 'This test required to specify a locan Anaconda Environment'
from examplecondaapp.exampleapp import AnacondaEnvironmentInfo
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



