"""
This is a template to create an EnMAP-Box test
"""
import unittest

from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsApplication, QgsRasterLayer, QgsVectorLayer
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from enmapbox import EnMAPBox


class EnMAPBoxTestCaseExample(EnMAPBoxTestCase):

    def test_testenvironment(self):
        # this example shows you the standard environment of an EnMAPBoxTestCase

        # QGIS is up and running
        qgsApp = QgsApplication.instance()
        self.assertIsInstance(qgsApp, QgsApplication)
        self.assertTrue(qgsApp == QApplication.instance())

        self.assertTrue(EnMAPBox.instance() is None)  # EnMAPBox is not started

        DIR_TEMP = self.tempDir()
        print(f'Place for temporary outputs: {DIR_TEMP}')

    def test_with_enmapbox(self):
        enmapBox = EnMAPBox()

        self.assertIsInstance(enmapBox, EnMAPBox)
        self.assertEqual(enmapBox, EnMAPBox.instance())
        enmapBox.loadExampleData()

        # generate in-memory test layers
        rasterLayer = TestObjects.createRasterLayer()
        self.assertIsInstance(rasterLayer, QgsRasterLayer)
        self.assertTrue(rasterLayer.isValid())

        vectorLayer = TestObjects.createVectorLayer()
        self.assertIsInstance(vectorLayer, QgsVectorLayer)
        self.assertTrue(vectorLayer.isValid())


if __name__ == '__main__':
    unittest.main(buffer=False)
