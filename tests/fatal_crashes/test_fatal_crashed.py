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

import unittest

from enmapbox.exampledata import enmap, hires
from enmapbox.gui.dataviews.dockmanager import DockManager, DockPanelUI, MapDockTreeNode, \
    DockManagerTreeModel
from enmapbox.gui.dataviews.docks import MapDock, DockArea
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from qgis.PyQt.QtCore import QMimeData, QModelIndex
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsLayerTreeLayer, QgsProject, QgsRasterLayer, QgsLayerTree
from qgis.gui import QgsMapCanvas


class TestDocksAndDataSources(EnMAPBoxTestCase):
    wmsUri = r'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
    wmsUri = r'referer=OpenStreetMap%20contributors,%20under%20ODbL&type=xyz&url=http://tiles.wmflabs.org/hikebike/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=17&zmin=1'
    wfsUri = r'restrictToRequestBBOX=''1'' srsname=''EPSG:25833'' typename=''fis:re_postleit'' url=''http://fbinter.stadt-berlin.de/fb/wfs/geometry/senstadt/re_postleit'' version=''auto'''

    def test_dockmanager(self):
        lyr = TestObjects.createRasterLayer()

        DM = DockManager()
        dockArea = DockArea()
        DM.connectDockArea(dockArea)
        DMTM = DockManagerTreeModel(DM)
        dock: MapDock = DM.createDock('MAP')
        self.assertIsInstance(dock, MapDock)
        tree: QgsLayerTree = dock.layerTree()
        self.assertIsInstance(tree, QgsLayerTree)

        tree.addLayer(lyr)
        tree.removeLayer(lyr)

        del DMTM, DM, dockArea, tree, dock
        QgsProject.instance().takeMapLayer(lyr)
        return

        DM = DockManager()
        DMTM = DockManagerTreeModel(DM)

        self.assertEqual(DM.project(), DMTM.project())

        dockArea = DockArea()
        DM.connectDockArea(dockArea)

        self.assertTrue(len(DM) == 0)
        dock: MapDock = DM.createDock('MAP')
        self.assertIsInstance(dock, MapDock)
        tree: QgsLayerTree = dock.layerTree()
        proj = dock.mapCanvas().project()

        tree.addLayer(lyr)
        layers = dock.treeNode().mapLayers()

        tree.removeAllChildren()
        DMTM
        QgsProject.instance().removeAllMapLayers()
        return

        self.assertTrue(lyr.id() in QgsProject.instance().mapLayers().keys())

        self.assertIsInstance(DMTM, DockManagerTreeModel)

        mapNodes = DMTM.mapDockTreeNodes()
        self.assertTrue(len(mapNodes) == 1)
        mapNode = mapNodes[0]
        self.assertIsInstance(mapNode, MapDockTreeNode)
        c = mapNode.mapCanvas()
        self.assertIsInstance(c, QgsMapCanvas)
        self.assertTrue(lyr in c.layers())
        self.assertTrue(lyr.id() in mapNode.findLayerIds())

        ltn = mapNode.findLayer(lyr)
        self.assertIsInstance(ltn, QgsLayerTreeLayer)

        idx = DMTM.node2index(ltn)
        self.assertIsInstance(idx, QModelIndex)
        self.assertTrue(idx.isValid())

        mimeData = DMTM.mimeData([idx])
        self.assertIsInstance(mimeData, QMimeData)

        # cleanup
        tree.removeAllChildren()
        QgsProject.instance().removeAllMapLayers()

    def test_issue_881(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        dock: MapDock = enmapBox.onDataDropped([QgsRasterLayer(enmap, 'enmap')])
        dock.insertLayer(0, QgsRasterLayer(hires, 'hires'))

        self.showGui(enmapBox.ui)
        enmapBox.close()
        QApplication.processEvents()
        QgsProject.instance().removeAllMapLayers()

    def test_DockPanelUI(self):
        w = DockPanelUI()
        DM = DockManager()
        project = QgsProject()

        def message(msg: str):
            print(msg)

        dockArea = DockArea()
        DM.connectDockArea(dockArea)
        self.assertIsInstance(w, DockPanelUI)
        self.assertIsInstance(DM, DockManager)
        w.connectDockManager(DM)
        model = w.dockManagerTreeModel()
        model.setProject(project)
        model.messageEmitted.connect(message)
        root: QgsLayerTree = model.rootGroup()

        def printLayers():
            print(root.findLayers())

        def onAddedChildren(node, indexFrom, indexTo):
            print(f'Added {node} {indexFrom} {indexTo}')
            printLayers()

        def onRemovedChildren(node, indexFrom, indexTo):
            print(f'Removed {node} {indexFrom} {indexTo}')
            printLayers()

        def nodeWillRemoveChildren(node, indexFrom, indexTo):
            print(f'Will remove {node} {indexFrom} {indexTo}')
            printLayers()

        MAPDOCK: MapDock = DM.createDock('MAP')
        lyr1 = TestObjects.createRasterLayer()
        lyr1.setName('Layer 1')
        lyr2 = TestObjects.createVectorLayer()
        lyr2.setName('Layer 2')
        project.addMapLayers([lyr1, lyr2])

        MAPDOCK.addLayers([lyr1, lyr2])

        root.addedChildren.connect(onAddedChildren)
        root.removedChildren.connect(onRemovedChildren)
        root.willRemoveChildren.connect(nodeWillRemoveChildren)
        # DM.createDock('SPECLIB')
        # DM.createDock('WEBVIEW')
        self.showGui(w)

        root.removeAllChildren()
        project.removeAllMapLayers()
        QgsProject.instance().removeAllMapLayers()

    def test_zzzz_final_call(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        self.showGui(enmapBox.ui)

        enmapBox.close()
        self.assertTrue(True)
        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":
    unittest.main(buffer=False)
