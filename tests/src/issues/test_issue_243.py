"""
This is a template to create an EnMAP-Box test
"""
import unittest

from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsApplication, QgsRasterLayer, QgsVectorLayer
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from enmapbox import EnMAPBox


class TestIssue243Examples(EnMAPBoxTestCase):

    def test_Issze243(self):
        enmapBox = EnMAPBox()

        enmapBox.loadExampleData()
        enmapBox.createNewMapCanvas('2nd Map')
        self.showGui(enmapBox.ui)


if __name__ == '__main__':
    unittest.main(buffer=False)
