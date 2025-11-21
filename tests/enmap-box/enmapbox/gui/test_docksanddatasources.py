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

from enmapbox import initEnMAPBoxResources
from enmapbox.exampledata import landcover_polygon, enmap, hires
from enmapbox.gui.datasources.datasources import VectorDataSource, RasterDataSource
from enmapbox.gui.datasources.manager import DataSourceManager
from enmapbox.gui.dataviews.dockmanager import DockManager, SpeclibDockTreeNode, MapDockTreeNode, \
    DockTreeView, DockManagerTreeModel, createDockTreeNode, DockTreeNode
from enmapbox.gui.dataviews.docks import MapDock, DockArea, MimeDataDock, TextDock, SpectralLibraryDock, TextDockWidget, \
    Dock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.maptools import MapTools
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.dockarea.Dock import Dock as pgDock
from enmapbox.qgispluginsupport.qps.speclib.core import is_spectral_library
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.testing import EnMAPBoxTestCase, TestObjects, start_app
from enmapboxtestdata import classificationDatasetAsPklFile, library_berlin
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsLayerTreeModel, QgsLayerTree
from qgis.gui import QgsMapCanvas, QgsLayerTreeView

start_app()
initEnMAPBoxResources()


class TestDocksAndDataSources(EnMAPBoxTestCase):
    wmsUri = r'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
    wmsUri = 'referer=OpenStreetMap%20contributors,%20under%20ODbL&type=xyz&url=http://tiles.wmflabs.org/hikebike/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=17&zmin=1'

    def test_dataSourceManager(self):

        signalArgs = []

        def onSignal(dataSource):
            signalArgs.extend(dataSource)

        DSM = DataSourceManager()
        self.assertIsInstance(DSM, DataSourceManager)
        DSM.sigDataSourcesAdded.connect(onSignal)

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

    def test_dock_cleanup(self):

        eb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        eb.loadExampleData()
        QApplication.processEvents()
        if True:
            pt = SpatialPoint.fromMapCanvasCenter(eb.mapCanvas())
            eb.setMapTool(MapTools.SpectralProfile)
            eb.setCurrentLocation(pt)
        eb.createSpectralLibraryDock(name='SL1')

        # self.showGui(eb.ui)
        # eb.close()
        for dock in eb.dockManager().docks():
            eb.dockManager().removeDock(dock)
            del dock

        QApplication.processEvents()

        assert len(eb.docks()) == 0
        QApplication.processEvents()
        import gc
        gc.collect()
        for d in [d for d in gc.get_objects() if
                  isinstance(d, (Dock, DockTreeNode, SpectralLibraryWidget))]:
            for r in gc.get_referrers(d):
                for r2 in gc.get_referrers(r):
                    for r3 in gc.get_referrers(r2):
                        s = ""

            raise Exception(f'Instance not garbage collected: {type(d)} = {d}')

        self.showGui(eb.ui)

    def test_SpeclibDockNodes(self):

        TV = DockTreeView(None)
        dsm = DataSourceManager()
        dm = DockManager()
        dm.connectDataSourceManager(dsm)
        dockArea = DockArea()
        dm.connectDockArea(dockArea)
        dm.connectDataSourceManager(dsm)
        model = DockManagerTreeModel(dm)
        TV.setModel(model)
        self.assertIsInstance(TV, QgsLayerTreeView)
        speclibDock: SpectralLibraryDock = dm.createDock(SpectralLibraryDock)

        node1: SpeclibDockTreeNode = model.findDockNode(speclibDock)
        node2: SpeclibDockTreeNode = model.findDockNode(speclibDock.speclibWidget())

        w = QWidget()
        l = QHBoxLayout()
        l.addWidget(TV)
        l.addWidget(dockArea)
        w.setLayout(l)
        self.showGui(w)
        QgsProject.instance().removeAllMapLayers()

    def test_ActionNode(self):

        TV = DockTreeView(None)

        self.showGui(TV)

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

        del view, model, manager, root

        project.removeAllMapLayers()
        QgsProject.instance().removeAllMapLayers()

    def test_pgDock(self):

        da = DockArea()

        dock = pgDock('Test')
        da.addDock(dock)
        da.show()
        self.showGui(da)
        QgsProject.instance().removeAllMapLayers()

    def test_MimeDataDock(self):
        da = DockArea()
        dock = MimeDataDock()
        da.addDock(dock)
        self.showGui(da)

        QgsProject.instance().removeAllMapLayers()

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

        QgsProject.instance().removeAllMapLayers()

    def test_SpeclibDock(self):

        # w = SpectralLibraryWidget()
        # self.showGui(w)
        da = DockArea()
        dock = SpectralLibraryDock()

        # self.assertTrue(is_spectral_library(dock.speclib()))
        self.showGui(dock)
        da.addDock(dock)
        self.assertIsInstance(dock, SpectralLibraryDock)
        self.showGui(da)

        QgsProject.instance().removeAllMapLayers()

    def test_MapDock(self):
        da = DockArea()
        from enmapbox.gui.dataviews.docks import MapDock
        dock = MapDock()
        self.assertIsInstance(dock, MapDock)
        da.addDock(dock)
        self.showGui(da)

        del da, dock

        QgsProject.instance().removeAllMapLayers()

    def test_SpeclibDockTreeNode(self):

        sl1 = TestObjects.createSpectralLibrary(name='speclib1')
        sl2 = TestObjects.createSpectralLibrary(name='speclib2')

        dock = SpectralLibraryDock()
        node = createDockTreeNode(dock)
        self.assertIsInstance(node, SpeclibDockTreeNode)
        slw = node.speclibWidget()
        slw.plotModel()
        self.assertIsInstance(slw, SpectralLibraryWidget)
        s = ""

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

        EMB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_issue_881(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        dock: MapDock = enmapBox.onDataDropped([QgsRasterLayer(enmap, 'enmap')])
        dock.insertLayer(0, QgsRasterLayer(hires, 'hires'))

        self.showGui(enmapBox.ui)
        enmapBox.close()
        QApplication.processEvents()
        QgsProject.instance().removeAllMapLayers()

    def test_issue_737(self):

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)

        enmapBox.addSource(classificationDatasetAsPklFile)
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
        mapDocks = eb.dockManager().docks(MapDock)

        self.assertIsInstance(tv, DockTreeView)

        self.showGui(eb.ui)
        eb.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":
    unittest.main(buffer=False)
