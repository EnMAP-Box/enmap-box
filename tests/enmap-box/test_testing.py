# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'

import unittest

from qgis.PyQt.QtGui import QGuiApplication
from qgis.PyQt.QtWidgets import QMenu
from osgeo import gdal, ogr
from qgis.gui import QgisInterface
from qgis.core import QgsProcessingAlgorithm, QgsApplication

from enmapbox.testing import EnMAPBoxTestCase, TestObjects


class Tests(EnMAPBoxTestCase):

    def setUp(self):
        self.closeEnMAPBoxInstance()

    def tearDown(self):
        self.closeEnMAPBoxInstance()

    def test_inMemoryImage(self):
        self.assertIsInstance(TestObjects.createRasterDataset(), gdal.Dataset)

    def test_inMemoryVector(self):
        ds = TestObjects.createVectorDataSet()
        self.assertIsInstance(ds, ogr.DataSource)
        self.assertTrue(ds.GetLayerCount() == 1)
        self.assertIsInstance(ds.GetLayerByIndex(0), ogr.Layer)
        self.assertTrue(ds.GetLayerByIndex(0).GetFeatureCount() > 0)

    def test_enmapboxApplication(self):

        from enmapbox.gui.enmapboxgui import EnMAPBox
        from enmapbox.gui.applications import EnMAPBoxApplication

        emb = EnMAPBox.instance()
        if not isinstance(emb, EnMAPBox):
            emb = EnMAPBox(None)

        ea = TestObjects.enmapboxApplication()
        self.assertIsInstance(ea, EnMAPBoxApplication)
        parentMenu = QMenu()
        self.assertIsInstance(ea.menu(parentMenu), QMenu)

        self.assertIsInstance(ea.processingAlgorithms(), list)
        for a in ea.processingAlgorithms():
            self.assertIsInstance(a, QgsProcessingAlgorithm)

    def test_initQgsApplication(self):
        app = QgsApplication.instance()
        self.assertIsInstance(app, QGuiApplication)

        import qgis.utils
        self.assertIsInstance(qgis.utils.iface, QgisInterface)


if __name__ == "__main__":
    unittest.main(buffer=False)
