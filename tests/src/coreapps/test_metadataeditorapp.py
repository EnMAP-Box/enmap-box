# -*- coding: utf-8 -*-

"""
***************************************************************************


    Some unit tests to check exampleapp components
    ---------------------
    Date                 : March 2018
    Copyright            : (C) 2018 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import datetime
import unittest
from osgeo import gdal, ogr
from enmapbox import initPythonPaths, EnMAPBox
from enmapbox.exampledata import landcover_polygon, enmap
from enmapbox.testing import TestObjects, EnMAPBoxTestCase
from metadataeditorapp.metadataeditor import MetadataEditorDialog
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject

initPythonPaths()


class MetadataEditorTests(EnMAPBoxTestCase):
    @classmethod
    def setUpClass(cls):
        from enmapbox.testing import initQgisApplication
        cls.qgsApp = initQgisApplication()

    @classmethod
    def tearDownClass(cls):
        cls.qgsApp.quit()

    def setUp(self):
        self.dsR = gdal.Open(enmap)
        self.dsV = ogr.Open(landcover_polygon)

        drv = gdal.GetDriverByName('MEM')
        self.dsRM = drv.CreateCopy('', self.dsR)

        drv = ogr.GetDriverByName('Memory')
        self.dsVM = drv.CopyDataSource(self.dsV, '')

    def createSupportedSources(self) -> list:
        from enmapbox.exampledata import enmap, landcover_polygon

        sources = []

        p1 = '/vsimem/tmp.enmap'
        to = gdal.TranslateOptions(format='ENVI')
        gdal.Translate(p1, enmap, options=to)
        sources.append(QgsRasterLayer(p1))

        sources.append(QgsVectorLayer(landcover_polygon))
        return sources

    def createNotSupportedSources(self) -> list:
        sources = []
        sources.append(__file__)
        return sources

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking Dialog')
    def test_MDDialog_QgsProject(self):
        from enmapbox.exampledata import hires

        layers = [TestObjects.createRasterLayer(nb=30),
                  TestObjects.createVectorLayer(),
                  TestObjects.createRasterLayer(nc=5),
                  QgsRasterLayer(),
                  QgsRasterLayer(hires, 'HiRes A'),
                  QgsRasterLayer(hires, 'HiRes B'),
                  QgsRasterLayer(enmap, 'EnMAP'),
                  ]

        d = MetadataEditorDialog()
        self.assertIsInstance(d, MetadataEditorDialog)
        d.show()
        QgsProject.instance().addMapLayers(layers)
        self.showGui(d)

    def test_speed(self):
        from enmapbox.exampledata import enmap

        lyr = QgsRasterLayer(enmap, 'EnMAP')

        d = MetadataEditorDialog()
        self.assertIsInstance(d, MetadataEditorDialog)
        d.show()
        QgsProject.instance().addMapLayer(lyr)

        t0 = datetime.datetime.now()
        # d.setLayer(lyr)
        dt = datetime.datetime.now() - t0

        self.showGui(d)

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking Dialog')
    def test_MDDialog_EnMAPBox(self):
        emb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        emb.loadExampleData()
        d = MetadataEditorDialog()
        d.setEnMAPBox(emb)

        self.showGui(d)


if __name__ == "__main__":
    unittest.main(buffer=False)
