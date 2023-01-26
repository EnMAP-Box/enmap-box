# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'
__date__ = '2017-07-17'
__copyright__ = 'Copyright 2017, Benjamin Jakimow'

import os
import pathlib
import unittest

import enmapbox.gui.mimedata as mimedata
from enmapbox import DIR_EXAMPLEDATA
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.exampledata import enmap, hires, library_gpkg, landcover_polygon
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt.QtCore import QMimeData, QByteArray, QUrl, Qt, QPoint
from qgis.PyQt.QtGui import QDropEvent
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsProject, QgsMapLayer, QgsRasterLayer, QgsVectorLayer
from qgis.core import QgsProviderRegistry


class MimeDataTests(EnMAPBoxTestCase):

    def setUp(self):

        super().setUp()
        box = EnMAPBox.instance()
        if isinstance(box, EnMAPBox):
            box.close()
        QApplication.processEvents()
        QgsProject.instance().removeAllMapLayers()

    def tearDown(self):
        super().tearDown()
        box = EnMAPBox.instance()
        if isinstance(box, EnMAPBox):
            box.close()
        QApplication.processEvents()
        QgsProject.instance().removeAllMapLayers()

    def test_conversions(self):
        for t1 in ['normalstring', b'bytestring', r'rawstring']:

            ba = mimedata.textToByteArray(t1)
            self.assertIsInstance(ba, QByteArray)
            t2 = mimedata.textFromByteArray(ba)
            self.assertIsInstance(t2, str)
            self.assertEqual(len(t1), len(t2))
            if isinstance(t1, bytes):
                self.assertEqual(t1.decode(), t2)
            else:
                self.assertEqual(t1, t2)

    def test_datasourcehandling(self):

        from enmapbox.gui.datasources.datasources import DataSource
        from enmapbox.gui.datasources.manager import DataSourceFactory

        dataSources = DataSourceFactory.create([enmap, hires, library_gpkg, landcover_polygon])
        dataSourceObjectIDs = [id(ds) for ds in dataSources]

        md = mimedata.fromDataSourceList(dataSources)

        self.assertIsInstance(md, QMimeData)

        sources = mimedata.toDataSourceList(md)
        self.assertEqual(len(sources), len(dataSources))
        for ds in dataSources:
            self.assertTrue(ds in sources)

        for src in sources:
            self.assertIsInstance(src, DataSource)
            self.assertTrue(src in dataSources)
            self.assertTrue(id(src) not in dataSourceObjectIDs)

    def test_maplayerhandling(self):

        mapLayers = [QgsRasterLayer(enmap), QgsVectorLayer(landcover_polygon)]
        md = mimedata.fromLayerList(mapLayers)

        self.assertIsInstance(md, QMimeData)
        self.assertTrue(mimedata.MDF_QGIS_LAYERTREEMODELDATA in md.formats())

        layers = mimedata.extractMapLayers(md)
        for lyr in layers:
            self.assertIsInstance(lyr, QgsMapLayer)
            self.assertTrue(lyr)

    def file2DropEvent(self, path) -> QDropEvent:
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        md = QMimeData()
        md.setUrls([QUrl.fromLocalFile(path.as_posix())])
        print('Drop {}'.format(path.name))
        self._mdref = md
        return QDropEvent(QPoint(0, 0), Qt.CopyAction, md, Qt.LeftButton, Qt.NoModifier)

    def test_dropping_files_empty_dockarea(self):

        import datetime
        t0 = datetime.datetime.now()
        p = r'\\141.20.140.91\san\_EnMAP\Rohdaten\EnmapBoxExternalSensorProducts'
        os.path.isdir(p)
        print(datetime.datetime.now() - t0)

        files = []
        nMax = 25
        for root, dirs, f in os.walk(DIR_EXAMPLEDATA):
            if len(files) >= nMax:
                break
            for file in f:
                files.append(pathlib.Path(root) / file)

        # drop on
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        dockManager = EB.dockManager()
        dockArea = dockManager.currentDockArea()
        for path in files:

            sublayers = QgsProviderRegistry.instance().querySublayers(path.as_posix())
            if len(sublayers) != 1:
                continue
            print(f'Drop {path}...', flush=True)
            dockManager.onDockAreaDragDropEvent(dockArea, self.file2DropEvent(path))
            QApplication.processEvents()
            for d in dockManager.docks():
                dockManager.removeDock(d)
            EB.dataSourceManager().removeDataSources(EB.dataSourceManager().dataSources())
            QApplication.processEvents()
            QgsProject.instance().removeAllMapLayers()
            QApplication.processEvents()

        print('Done!')
        EB.close()


if __name__ == "__main__":
    unittest.main(buffer=False)
