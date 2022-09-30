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

import pathlib
import unittest

from enmapbox import EnMAPBox
from enmapbox.exampledata import enmap, hires, landcover_polygon, library_gpkg
from enmapbox.gui.dataviews.dockmanager import MapDockTreeNode, MapCanvasBridge
from enmapbox.gui.dataviews.docks import MapDock
from enmapbox.gui.mapcanvas import CanvasLink, MapCanvas, KEY_LAST_CLICKED, LINK_ON_CENTER
from enmapbox.qgispluginsupport.qps.maptools import CursorLocationMapTool, MapTools
from enmapbox.testing import EnMAPBoxTestCase
from enmapbox.testing import TestObjects
from qgis.PyQt.QtCore import QMimeData, QUrl
from qgis.PyQt.QtGui import QKeyEvent
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.core import QgsPointXY, QgsProject, QgsRasterLayer


class MapCanvasTests(EnMAPBoxTestCase):

    def setUp(self) -> None:
        QgsProject.instance().removeAllMapLayers()

    def test_mapDock(self):
        dock = MapDock()
        self.assertIsInstance(dock, MapDock)
        m1 = QMenu()
        m = dock.populateContextMenu(m1)
        self.assertIsInstance(m, QMenu)
        self.assertTrue(m == m1)

    def test_mapCanvas(self):
        mapCanvas = MapCanvas()
        lyr = TestObjects.createRasterLayer()
        self.assertTrue(lyr not in QgsProject.instance().mapLayers().values())
        QgsProject.instance().addMapLayer(lyr)
        mapCanvas.setLayers([lyr])
        mapCanvas.setDestinationCrs(lyr.crs())
        mapCanvas.zoomToFullExtent()

        # self.assertTrue(lyr in QgsProject.instance().mapLayers().values())
        self.assertTrue(lyr in mapCanvas.layers())
        menu = QMenu()
        mapCanvas.populateContextMenu(menu, None)
        self.assertIsInstance(menu, QMenu)
        actions = [a for a in menu.children() if isinstance(a, QAction)]
        self.assertTrue(len(actions) > 2)

        mapCanvas.mapTools().activate(MapTools.CursorLocation)

        def onLocationSelected():
            print('Location Selected')

        def onKeyPressed(e: QKeyEvent):
            print('Key pressed')

        mapCanvas.mapTools().mtCursorLocation.sigLocationRequest.connect(onLocationSelected)
        mapCanvas.keyPressed.connect(onKeyPressed)

        self.showGui(mapCanvas)

    def test_canvaslinks(self):
        canvases = []
        for i in range(3):
            c = MapCanvas()
            lyr = QgsRasterLayer(enmap)
            QgsProject.instance().addMapLayer(lyr)
            c.setLayers([lyr])
            c.setDestinationCrs(lyr.crs())
            c.setExtent(lyr.extent())
            center0 = c.center()
            center0.setX(center0.x() + 10 * i)
            c.setCenter(center0)
            canvases.append(c)
            self.assertIsInstance(c, MapCanvas)
            self.assertIsInstance(c.property(KEY_LAST_CLICKED), float)
        c1, c2, c3 = canvases

        center0 = c1.center()
        CanvasLink(c1, c2, CanvasLink.LINK_ON_CENTER_SCALE)
        CanvasLink(c1, c3, CanvasLink.LINK_ON_CENTER_SCALE)
        CanvasLink.GLOBAL_LINK_LOCK = False
        self.assertTrue(c1.center() == center0)
        self.assertTrue(c2.center() == center0)
        self.assertTrue(c3.center() == center0)

        center1 = QgsPointXY(center0)
        center1.setX(center1.x() + 200)
        center2 = QgsPointXY(center0)
        center2.setX(center1.x() + 300)
        center3 = QgsPointXY(center0)
        center3.setX(center1.x() + 400)

        c1.extentsChanged.connect(lambda: print('Extent C1 changed'))
        c2.extentsChanged.connect(lambda: print('Extent C1 changed'))
        c3.extentsChanged.connect(lambda: print('Extent C1 changed'))

        c1.setCenter(center1)
        self.assertTrue(c1.center() == center1)
        self.assertTrue(c2.center() == center1)
        self.assertTrue(c3.center() == center1)

        c2.setCenter(center2)
        self.assertTrue(c1.center() == center2)
        self.assertTrue(c2.center() == center2)
        self.assertTrue(c3.center() == center2)

        c3.setCenter(center3)
        self.assertTrue(c1.center() == center3)
        self.assertTrue(c2.center() == center3)
        self.assertTrue(c3.center() == center3)

    def test_mapCrosshairDistance(self):

        lyrWorld = QgsRasterLayer(TestObjects.uriWMS(), 'Background', 'wms')
        lyrEnMAP = TestObjects.createRasterLayer()
        assert lyrEnMAP.isValid()
        layers = [lyrEnMAP, lyrWorld]

        canvas = MapCanvas()
        canvas.setProject(QgsProject.instance())
        mt = CursorLocationMapTool(canvas)
        canvas.setMapTool(mt)
        canvas.setLayers(layers)
        if True:
            canvas.setDestinationCrs(lyrEnMAP.crs())
            canvas.setExtent(lyrEnMAP.extent())
        else:
            canvas.zoomToProjectExtent()
        canvas.setCrosshairVisibility(True)
        self.showGui(canvas)

    def test_mapLinking(self):

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)

        map1: MapDock = enmapBox.createDock('MAP')
        map2: MapDock = enmapBox.createDock('MAP')
        link = map1.linkWithMapDock(mapDock=map2, linkType=LINK_ON_CENTER)
        self.assertIsInstance(link, CanvasLink)
        self.showGui(enmapBox.ui)

    def test_dropEvents(self):

        mapDock = MapDock()
        node = MapDockTreeNode(mapDock)
        bridge = MapCanvasBridge(node, mapDock.mapCanvas())
        mapCanvas = mapDock.mapCanvas()
        allFiles = [enmap, hires, landcover_polygon, library_gpkg]
        spatialFiles = [enmap, hires, landcover_polygon]

        md = QMimeData()
        md.setUrls([QUrl.fromLocalFile(f) for f in allFiles])

        # drop URLs
        mapCanvas.setLayers([])
        mapCanvas.dropEvent(TestObjects.createDropEvent(md))
        # self.assertTrue(len(self.mapCanvas.layerPaths()) == len(spatialFiles))

        layerPaths = [pathlib.Path(p) for p in mapCanvas.layerPaths()]
        for p in spatialFiles:
            self.assertTrue(pathlib.Path(p) in layerPaths)


if __name__ == "__main__":
    unittest.main(buffer=False)
