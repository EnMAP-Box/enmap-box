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

import importlib
import os
import unittest

from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer

from enmapbox import initEnMAPBoxResources
from enmapbox.exampledata import landcover_polygon, enmap
from enmapbox.gui.datasources.datasources import VectorDataSource, RasterDataSource
from enmapbox.gui.datasources.manager import DataSourceManager
from enmapbox.gui.dataviews.dockmanager import (
    DockTreeView, DockTreeNode
)
from enmapbox.gui.dataviews.docks import (
    Dock
)
from enmapbox.gui.dataviews.mapdock import MapDock
from enmapbox.gui.dataviews.webviewdock import WebViewDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.maptools import MapTools
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.testing import EnMAPBoxTestCase, TestObjects, start_app

start_app()
initEnMAPBoxResources()


class TestDocksAndDataSources(EnMAPBoxTestCase):
    wmsUri = (
        r'crs=EPSG:3857&format&type=xyz&url='
        r'https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
    )
    wmsUri = (
        'referer=OpenStreetMap%20contributors,%20under%20ODbL&type=xyz&url='
        'http://tiles.wmflabs.org/hikebike/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=17&zmin=1'
    )

    def test_dataSourceManager(self):

        signalArgs = []

        def onSignal(dataSource):
            signalArgs.extend(dataSource)

        DSM = DataSourceManager()
        self.assertIsInstance(DSM, DataSourceManager)
        DSM.sigDataSourcesAdded.connect(onSignal)
        from enmapboxtestdata import library_berlin
        DSM.addDataSources(enmap)
        DSM.addDataSources(landcover_polygon)
        DSM.addDataSources(library_berlin)

        self.assertTrue(len(signalArgs) == 3)
        self.assertIsInstance(signalArgs[0], RasterDataSource)
        self.assertIsInstance(signalArgs[1], VectorDataSource)

        sources = DSM.dataSources(filter=[RasterDataSource])
        self.assertTrue(len(sources) == 1)
        self.assertIsInstance(sources[0], RasterDataSource)

        sources = DSM.dataSources(filter=[RasterDataSource, VectorDataSource])
        self.assertEqual(len(sources), 3)
        self.assertIsInstance(sources[0], RasterDataSource)
        self.assertIsInstance(sources[1], VectorDataSource)
        self.assertIsInstance(sources[2], VectorDataSource)

        self.assertEqual(len(DSM.dataSources()), 3)
        sources = DSM.dataSources(filter=RasterDataSource)
        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], RasterDataSource)
        self.assertIs(sources[0], signalArgs[0])

        sources = DSM.dataSources(filter=VectorDataSource)
        self.assertTrue(len(sources) == 2)
        self.assertIsInstance(sources[0], VectorDataSource)
        self.assertIs(sources[0], signalArgs[1])

        lyrWMS = QgsRasterLayer(TestObjects.uriWMS(), 'WMS', 'wms')
        if lyrWMS.isValid():
            for o in [lyrWMS]:
                sources = DSM.addDataSources(o)
                self.assertEqual(len(sources), 1)
                self.assertIsInstance(sources[0], RasterDataSource)
                DSM.removeDataSources(sources)

        QgsProject.instance().removeAllMapLayers()

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'Manual testing only')
    def test_dock_cleanup(self):

        import gc
        gc.collect()
        for d in [d for d in gc.get_objects() if
                  isinstance(d, (Dock, DockTreeNode, SpectralLibraryWidget))]:
            self.fail(f'Instance not garbage collected: {type(d)} = {d}')

        eb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        eb.loadExampleData()
        QApplication.processEvents()
        if True:
            pt = SpatialPoint.fromMapCanvasCenter(eb.mapCanvas())
            eb.setMapTool(MapTools.SpectralProfile)
            eb.setCurrentLocation(pt)
        eb.createSpectralLibraryDock(name='SL1')

        for dock in eb.dockManager().docks():
            eb.dockManager().removeDock(dock)
            del dock

        QApplication.processEvents()

        self.assertEqual(eb.docks(), 0)
        QApplication.processEvents()

        gc.collect()
        for d in [d for d in gc.get_objects() if
                  isinstance(d, (Dock, DockTreeNode, SpectralLibraryWidget))]:
            for r in gc.get_referrers(d):
                for r2 in gc.get_referrers(r):
                    for r3 in gc.get_referrers(r2):
                        pass

            raise Exception(f'Instance not garbage collected: {type(d)} = {d}')

        self.showGui(eb.ui)

    def test_ActionNode(self):

        TV = DockTreeView(None)

        self.showGui(TV)

    has_QtWebEngineWidgets = importlib.util.find_spec('qgis.PyQt.QtWebEngineWidgets') is not None
    runs_offscreen = os.environ.get('QT_QPA_PLATFORM', '').lower() in ['offscreen']

    @unittest.skipIf(runs_offscreen, 'QT_QPA_PLATFORM=offscreen. QWebEngineView requires a screen device')
    @unittest.skipIf(not has_QtWebEngineWidgets, 'qgis.PyQt.QtWebEngineWidgets not available')
    def test_WebViewDock(self):
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Home page</title>
        </head>
        <body>
            <p>
                This is a simple HTML page.
            </p>
        </body>
        </html>
        """

        # from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
        # view = QWebEngineView()
        # view.setWindowTitle('Test')

        # view.setHtml(html)
        # self.showGui(view)

        dock = WebViewDock()
        dock.showHtml(html)
        self.showGui(dock)

    def test_issue_737(self):

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        from enmapboxtestdata import classificationDatasetAsSkopsFile
        enmapBox.addSource(classificationDatasetAsSkopsFile)
        self.showGui(enmapBox.ui)

        enmapBox.close()
        QgsProject.instance().removeAllMapLayers()

    def test_dockTreeViewDoubleClicks(self):
        eb = EnMAPBox(load_core_apps=False, load_other_apps=False)

        lyrR = QgsRasterLayer(enmap)
        lyrV = QgsVectorLayer(landcover_polygon)

        mapDock1 = eb.createDock('MAP')
        self.assertIsInstance(mapDock1, MapDock)
        mapDock1.mapCanvas().setLayers([lyrR, lyrV])
        tv = eb.dockTreeView()
        mapDock2 = eb.createDock('MAP')
        self.assertIsInstance(mapDock2, MapDock)
        eb.setCurrentMapCanvas(mapDock2.mapCanvas())
        eb.dockManager().docks(MapDock)

        self.assertIsInstance(tv, DockTreeView)

        self.showGui(eb.ui)
        eb.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":
    unittest.main(buffer=False)
