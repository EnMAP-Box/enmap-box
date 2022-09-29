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
import tempfile
import unittest

from qgis.PyQt.QtCore import QMimeData, QModelIndex
from qgis.core import QgsLayerTreeLayer, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsLayerTreeModel, QgsLayerTree
from qgis.gui import QgsMapCanvas, QgsLayerTreeView

from enmapbox import EnMAPBox
from enmapbox.exampledata import landcover_polygon, library_gpkg, enmap, hires
from enmapbox.gui.datasources.datasources import VectorDataSource, RasterDataSource
from enmapbox.gui.datasources.manager import DataSourceManager
from enmapbox.gui.dataviews.dockmanager import DockManager, DockPanelUI, SpeclibDockTreeNode, MapDockTreeNode, \
    DockTreeView, DockManagerTreeModel
from enmapbox.gui.dataviews.docks import MapDock, DockArea, MimeDataDock, TextDock, SpectralLibraryDock, TextDockWidget
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.dockarea.Dock import Dock as pgDock
from enmapbox.qgispluginsupport.qps.speclib.core import is_spectral_library
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from enmapboxtestdata import classificationDatasetAsPklFile


class TestDocksAndDataSources(EnMAPBoxTestCase):

    def setUp(self):
        super().setUp()
        self.wmsUri = r'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
        self.wmsUri = 'referer=OpenStreetMap%20contributors,%20under%20ODbL&type=xyz&url=http://tiles.wmflabs.org/hikebike/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=17&zmin=1'
        self.wfsUri = r'restrictToRequestBBOX=''1'' srsname=''EPSG:25833'' typename=''fis:re_postleit'' url=''http://fbinter.stadt-berlin.de/fb/wfs/geometry/senstadt/re_postleit'' version=''auto'''

    def tearDown(self):
        self.closeEnMAPBoxInstance()
        super().tearDown()

    def test_dataSourceManager(self):

        global signalArgs
        signalArgs = []

        def onSignal(dataSource):
            signalArgs.extend(dataSource)

        DSM = DataSourceManager()
        self.assertIsInstance(DSM, DataSourceManager)
        DSM.sigDataSourcesAdded.connect(onSignal)

        DSM.addDataSources(enmap)
        DSM.addDataSources(landcover_polygon)
        DSM.addDataSources(library_gpkg)

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

        lyrWFS = QgsVectorLayer(TestObjects.uriWFS(), 'WFS', 'WFS')
        if lyrWFS.isValid():
            for o in [lyrWFS]:
                sources = DSM.addDataSources(o)
                self.assertEqual(len(sources), 1)
                self.assertIsInstance(sources[0], VectorDataSource)
                DSM.removeDataSources(sources)

        lyrWMS = QgsRasterLayer(TestObjects.uriWMS(), 'WMS', 'wms')
        if lyrWMS.isValid():
            for o in [lyrWMS]:
                sources = DSM.addDataSources(o)
                self.assertEqual(len(sources), 1)
                self.assertIsInstance(sources[0], RasterDataSource)
                DSM.removeDataSources(sources)

    def test_dockview(self):
        TV = DockTreeView(None)
        self.assertIsInstance(TV, QgsLayerTreeView)

    def test_dockmanager(self):

        lyr = TestObjects.createRasterLayer()

        self.assertTrue(lyr.id() not in QgsProject.instance().mapLayers().keys())

        DM = DockManager()

        self.assertTrue(len(DM) == 0)
        dock = DM.createDock('MAP')
        self.assertIsInstance(dock, MapDock)
        dock.mapCanvas().setLayers([lyr])
        self.assertTrue(lyr.id() in QgsProject.instance().mapLayers().keys())

        DMTM = DockManagerTreeModel(DM)
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

    def test_canvasBridge(self):
        project = QgsProject()
        lyr1 = TestObjects.createVectorLayer()
        lyr1.setName('Layer 1')
        lyr2 = TestObjects.createVectorLayer()
        lyr2.setName('Layer 2')
        layers = [lyr1, lyr2]
        project.addMapLayers(layers)
        widgets = []
        if False:
            treeRoot = QgsLayerTree()
            model = QgsLayerTreeModel(treeRoot)
            model.setFlag(QgsLayerTreeModel.AllowNodeReorder, True)
            model.setFlag(QgsLayerTreeModel.AllowNodeRename, True)
            model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility, True)
            model.setFlag(QgsLayerTreeModel.AllowLegendChangeState, True)
            model.setAutoCollapseLegendNodes(0)

            tree1 = QgsLayerTree()
            tree1.setName('Tree1')
            tree2 = QgsLayerTree()
            tree2.setName('Tree2')
            model.rootGroup().insertChildNodes(0, [tree1, tree2])
        else:
            manager = DockManager()
            dockArea = DockArea()
            manager.connectDockArea(dockArea)

            model = DockManagerTreeModel(manager)
            model.setProject(project)
            dock1 = manager.createDock('MAP', name='Tree1')
            dock2 = manager.createDock('MAP', name='Tree2')
            widgets.extend([dock1, dock2])
        root = model.rootGroup().children()[0]
        canvas = QgsMapCanvas()
        # bridge = QgsLayerTreeMapCanvasBridge(root, canvas)

        # view = QgsLayerTreeView()
        view = DockTreeView()
        view.setDragEnabled(True)
        view.setAcceptDrops(True)
        view.setModel(model)
        for lyr in layers:
            root.addLayer(lyr)
        widgets.insert(0, view)
        self.showGui(widgets)

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

    def test_pgDock(self):

        da = DockArea()

        dock = pgDock('Test')
        da.addDock(dock)
        da.show()
        self.showGui(da)

    def test_MimeDataDock(self):
        da = DockArea()
        dock = MimeDataDock()
        da.addDock(dock)
        self.showGui(da)

    def test_TextDock(self):
        da = DockArea()
        dock = TextDock()
        self.assertIsInstance(dock, TextDock)
        tw = dock.textDockWidget()
        self.assertIsInstance(tw, TextDockWidget)

        testText = """
        foo
        bar
        """
        tw.setText(testText)
        self.assertEqual(testText, tw.text())
        pathTxt = os.path.join(tempfile.gettempdir(), 'testfile.txt')
        tw.mFile = pathTxt
        tw.save()

        with open(pathTxt, encoding='utf-8') as f:
            checkTxt = f.read()
        self.assertEqual(checkTxt, testText)
        tw.mFile = None

        tw.setText('')
        self.assertEqual(tw.text(), '')
        tw.loadFile(pathTxt)
        self.assertEqual(checkTxt, tw.text())

        da.addDock(dock)
        da.show()
        self.showGui(da)

    def test_SpeclibDock(self):
        da = DockArea()
        dock = SpectralLibraryDock()
        self.assertTrue(is_spectral_library(dock.speclib()))
        da.addDock(dock)
        self.assertIsInstance(dock, SpectralLibraryDock)
        self.showGui(da)

    def test_MapDock(self):
        da = DockArea()
        from enmapbox.gui.dataviews.docks import MapDock
        dock = MapDock()
        self.assertIsInstance(dock, MapDock)
        da.addDock(dock)
        self.showGui(da)

    def test_MapDockLayerHandling(self):

        EMB = EnMAPBox(load_other_apps=False, load_core_apps=False)
        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())

        canvas1 = EMB.createNewMapCanvas('Canvas1')
        canvas2 = EMB.createNewMapCanvas('Canvas2')

        mapNode = EMB.findDockTreeNode(canvas2)
        self.assertIsInstance(mapNode, MapDockTreeNode)
        self.assertEqual(mapNode.mapCanvas(), canvas2)
        lyr = TestObjects.createRasterLayer()
        mapNode.addLayer(lyr)

        node = EMB.findDockTreeNode(lyr)
        self.assertIsInstance(node, MapDockTreeNode)
        self.assertTrue(lyr.id() in node.findLayerIds())

        speclib1 = EMB.createNewSpectralLibrary('Speclib 1')
        self.assertIsInstance(speclib1, QgsVectorLayer)
        self.assertTrue(is_spectral_library(speclib1))

        mapNode.addLayer(speclib1)
        node = EMB.findDockTreeNode(speclib1)
        self.assertTrue(node, SpeclibDockTreeNode)

    def test_issue_881(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        dock: MapDock = enmapBox.onDataDropped([QgsRasterLayer(enmap, 'enmap')])
        dock.insertLayer(0, QgsRasterLayer(hires, 'hires'))

        self.showGui(enmapBox.ui)
        enmapBox.close()

    def test_issue_737(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        enmapBox.addSource(classificationDatasetAsPklFile)
        self.showGui(enmapBox.ui)
        enmapBox.close()

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
        mapDocks = eb.dockManager().docks(MapDock)

        self.assertIsInstance(tv, DockTreeView)

        self.showGui(eb.ui)


if __name__ == "__main__":
    unittest.main(buffer=False)
