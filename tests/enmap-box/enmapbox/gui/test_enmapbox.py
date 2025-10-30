# -*- coding: utf-8 -*-
"""
***************************************************************************
    test_enmapbox.py
    ---------------------
    Date                 : Januar 2018
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
# noinspection PyPep8Naming
import pathlib
import unittest

import qgis
from enmapbox import DIR_REPO
from enmapbox.gui.contextmenus import EnMAPBoxContextMenuRegistry, EnMAPBoxAbstractContextMenuProvider
from enmapbox.gui.dataviews.docks import SpectralLibraryDock, MapDock, Dock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.qgispluginsupport.qps.maptools import MapTools
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.testing import TestObjects, EnMAPBoxTestCase, start_app
from qgis.PyQt.QtCore import QPoint
from qgis.PyQt.QtWidgets import QGridLayout, QWidget, QLabel
from qgis.PyQt.QtWidgets import QMenu
from qgis.core import Qgis, QgsExpressionContextGenerator, QgsProcessingContext, QgsExpressionContext
from qgis.core import QgsProject, QgsMapLayer, QgsRasterLayer, QgsVectorLayer, \
    QgsLayerTree, QgsApplication
from qgis.gui import QgsMapLayerComboBox, QgisInterface, QgsProcessingContextGenerator, QgsMapCanvas

start_app()


class EnMAPBoxTests(EnMAPBoxTestCase):

    @unittest.skipIf(not (pathlib.Path(DIR_REPO) / 'qgisresources').is_dir(), 'qgisresources dir does not exist')
    def test_find_qgis_resources(self):
        from enmapbox.qgispluginsupport.qps.resources import findQGISResourceFiles
        results = findQGISResourceFiles()
        if not self.runsInCI():
            print('Resource files found:')
            for p in results:
                print(p)
        self.assertTrue(len(results) > 0)

    def test_qgis_project_lists(self):

        from qgis.utils import iface
        lyrA = TestObjects.createVectorLayer()
        lyrB = TestObjects.createVectorLayer()
        lyrA.setName('VectorA')
        lyrB.setName('VectorB')
        QgsProject.instance().addMapLayers([lyrA, lyrB])

        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        EMB.loadExampleData()

        self.assertTrue(lyrA not in EMB.project().mapLayers().values())
        self.assertTrue(lyrB not in EMB.project().mapLayers().values())

        cbAll = QgsMapLayerComboBox()

        cbEnMAPBox = QgsMapLayerComboBox()
        cbEnMAPBox.setProject(EMB.project())

        w = QWidget()
        w.setWindowTitle('QProject layers')
        grid = QGridLayout()
        grid.addWidget(QLabel('QGIS'), 0, 0)
        grid.addWidget(QLabel('EnMAP-Box'), 1, 0)
        grid.addWidget(cbAll, 0, 1)
        grid.addWidget(cbEnMAPBox, 1, 1)
        w.setLayout(grid)
        self.showGui([EMB.ui, iface.ui, w])

        EMB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_instance_pure(self):
        EMB = EnMAPBox(load_other_apps=False, load_core_apps=False)

        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())

        mw = qgis.utils.iface.mainWindow()
        windows = [mw, EMB.ui]

        if True:
            w = QWidget()
            w.setWindowTitle('QProject layers')
            l = QGridLayout()
            w.setLayout(l)
            cbQGIS = QgsMapLayerComboBox()
            l.addWidget(QLabel('QGIS Layers'), 0, 0)
            l.addWidget(cbQGIS, 0, 1)

            if Qgis.versionInt() > 32400:
                cbEMB = QgsMapLayerComboBox()
                cbEMB.setWindowTitle('EnMAP-Box Layers')
                cbEMB.setProject(EMB.project())

                l.addWidget(QLabel('EnMAP-Box Layers'), 1, 0)
                l.addWidget(cbEMB, 1, 1)
            windows.append(w)
        self.showGui(windows)
        EMB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_context_interfaces(self):

        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        self.assertIsInstance(EMB, QgsExpressionContextGenerator)
        self.assertIsInstance(EMB, QgsProcessingContextGenerator)
        EMB.loadExampleData()
        QgsApplication.processEvents()
        canvas1 = EMB.currentMapCanvas()
        canvas2 = EMB.createNewMapCanvas('MyNewMapDock')
        self.assertIsInstance(canvas1, QgsMapCanvas)
        layers = canvas1.layers()
        self.assertTrue(len(layers) > 0)
        for lyr in layers:
            EMB.setCurrentLayer(lyr)
            self.assertTrue(EMB.currentLayer(), lyr)

            expression_context = EMB.createExpressionContext()
            self.assertIsInstance(expression_context, QgsExpressionContext)

            processing_context = EMB.processingContext()

            self.assertIsInstance(processing_context, QgsProcessingContext)
            self.assertEqual(processing_context.project(), EMB.project())
            self.assertEqual(lyr, processing_context.getMapLayer(lyr.id()))
            self.assertEqual(processing_context.transformContext(), EMB.project().transformContext())

        self.assertIsInstance(canvas2, QgsMapCanvas)
        self.assertTrue(canvas2.name(), 'MyNewMapDock')
        self.assertTrue(canvas1 != canvas2)
        EMB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_instance_all_apps(self):
        EMB = EnMAPBox(load_core_apps=True, load_other_apps=True)
        self.assertIsInstance(EMB, EnMAPBox)
        self.showGui(EMB.ui)
        EMB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_qgis_project_layers(self):

        from enmapbox.exampledata import enmap, landcover_polygon
        from qgis.utils import iface
        layers = [QgsRasterLayer(enmap), QgsVectorLayer(landcover_polygon)]
        # layers.append(QgsRasterLayer(WMS_OSM, 'osm', 'wms'))
        # layers.append(QgsVectorLayer(WFS_Berlin, 'wfs', 'WFS'))

        for lyr in layers:
            self.assertIsInstance(lyr, QgsMapLayer)
            self.assertTrue(lyr.isValid())

        self.assertIsInstance(iface, QgisInterface)
        QgsProject.instance().addMapLayers(layers)

        for layer in layers:
            self.assertIsInstance(layer, QgsMapLayer)

            iface.mapCanvas().setLayers([layer])
            iface.setActiveLayer(layer)
            self.assertEqual(iface.activeLayer(), layer)

        box = EnMAPBox(load_core_apps=False, load_other_apps=False)
        iface = qgis.utils.iface
        self.assertIsInstance(iface, QgisInterface)
        root = iface.layerTreeView().layerTreeModel().rootGroup()
        self.assertIsInstance(root, QgsLayerTree)

        self.assertTrue(len(box.dataSources()) == 0)

        lyrNew = TestObjects.createVectorLayer()
        QgsProject.instance().addMapLayer(lyrNew, True)
        QgsApplication.processEvents()

        self.assertEqual(len(box.dataSources()), 0)

        nQGIS = len(root.findLayerIds())
        box.dataSourceManager().importQGISLayers()
        QgsApplication.processEvents()
        self.assertEqual(len(box.dataSources()), nQGIS)

        QgsApplication.processEvents()

        self.assertEqual(len(box.dataSources()), nQGIS)
        self.showGui([box, iface.mainWindow()])

        layers_qgis = list(QgsProject.instance().mapLayers().values())

        for lyr in box.project().mapLayers().values():
            self.assertTrue(lyr in layers_qgis)

        mapDock: MapDock = box.createDock(MapDock)
        lyrNew = TestObjects.createVectorLayer()
        lyrNew.setName('MyNewLayer')
        mapDock.addLayers([lyrNew])

        cb1 = QgsMapLayerComboBox()
        n = cb1.model().rowCount()
        self.assertFalse(lyrNew in list(QgsProject.instance().mapLayers().values()))
        self.assertTrue(lyrNew in list(box.project().mapLayers().values()))
        mapDock.removeLayer(lyrNew)
        self.assertFalse(lyrNew in list(QgsProject.instance().mapLayers().values()))
        self.assertTrue(lyrNew in list(box.project().mapLayers().values()))
        QgsProject.instance().removeAllMapLayers()

    def test_createDock(self):

        EMB = EnMAPBox()
        for d in ['MAP', 'TEXT', 'SPECLIB', 'MIME']:
            dock = EMB.createDock(d)
            self.assertIsInstance(dock, Dock)
        self.showGui(EMB.ui)

        EMB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_RAISE_ALL_EXCEPTIONS(self):

        import enmapbox
        self.assertIsInstance(enmapbox.RAISE_ALL_EXCEPTIONS, bool)

        class TestException(Exception):

            def __init__(self, *args, **kwds):
                super().__init__(*args, **kwds)

        class ErrorProvider(EnMAPBoxAbstractContextMenuProvider):
            def __init__(self, *args, **kwds):
                super().__init__(*args, **kwds)

            def populateDataViewMenu(self, *args, **kwargs):
                raise TestException()

            def populateDataSourceMenu(self, *args, **kwargs):
                raise TestException()

            def populateMapCanvasMenu(self, *args, **kwargs):
                raise TestException()

        lastValue = enmapbox.RAISE_ALL_EXCEPTIONS

        reg0 = EnMAPBoxContextMenuRegistry.instance()
        reg = EnMAPBoxContextMenuRegistry()
        reg.addProvider(ErrorProvider())

        menu = QMenu()
        canvas = QgsMapCanvas()
        point = SpatialPoint.fromMapCanvasCenter(canvas)

        enmapbox.RAISE_ALL_EXCEPTIONS = True

        with self.assertRaises(TestException):
            reg.populateMapCanvasMenu(menu, canvas, QPoint(0, 0), point)

        enmapbox.RAISE_ALL_EXCEPTIONS = False

        reg.populateMapCanvasMenu(menu, canvas, QPoint(0, 0), point)

        enmapbox.RAISE_ALL_EXCEPTIONS = lastValue

    def test_addSources(self):
        E = EnMAPBox()
        E.loadExampleData()
        E.removeSources(E.dataSources())
        self.assertTrue(len(E.dataSources()) == 0)
        from enmapbox.exampledata import enmap, landcover_polygon
        E.addSource(enmap)
        self.assertTrue(len(E.dataSources()) == 1)
        E.addSource(landcover_polygon)
        self.assertTrue(len(E.dataSources()) == 2)

        self.showGui()

        E.close()
        QgsProject.instance().removeAllMapLayers()

    def test_mapCanvas(self):
        E = EnMAPBox()
        self.assertTrue(E.mapCanvas() is None)
        canvases = E.mapCanvases()
        self.assertIsInstance(canvases, list)
        self.assertTrue(len(canvases) == 0)

        # E.loadExampleData()
        # self.assertTrue(len(E.mapCanvases()) == 1)

        E.createDock('MAP')
        self.assertTrue(len(E.mapCanvases()) == 1)
        for c in E.mapCanvases():
            self.assertIsInstance(c, MapCanvas)

        self.showGui(E.ui)

        E.close()
        QgsProject.instance().removeAllMapLayers()

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking dialogs')
    def test_createNewLayers(self):

        E = EnMAPBox(load_core_apps=False, load_other_apps=False)
        E.ui.mActionCreateNewMemoryLayer.trigger()

        E.ui.mActionCreateNewShapefileLayer.trigger()

        E.ui.mActionCreateNewGeoPackageLayer.trigger()

        self.showGui(E.ui)

        E.close()
        QgsProject.instance().removeAllMapLayers()

    def test_loadExampleData_mapTools(self):
        E = EnMAPBox(load_core_apps=False, load_other_apps=False)
        E.loadExampleData()
        n = len(E.dataSources())
        self.assertTrue(n > 0)

        for mt in MapTools.mapToolEnums():
            E.setMapTool(mt)

        self.showGui(E.ui)

        E.close()
        QgsProject.instance().removeAllMapLayers()

    @unittest.skip('Disable project syncing for now')
    def test_loadAndUnloadData(self):

        E = EnMAPBox(load_core_apps=False, load_other_apps=False)

        def nQgis() -> int:
            return len(QgsProject.instance().mapLayers())

        def nSrc() -> int:
            return len(E.dataSources())

        mapDock = E.createDock('MAP')  # empty map
        self.assertIsInstance(mapDock, MapDock)
        self.assertEqual(nQgis(), 0)
        self.assertEqual(nSrc(), 0)

        lyrQGIS = TestObjects.createVectorLayer()
        QgsProject.instance().addMapLayer(lyrQGIS)
        self.assertEqual(nSrc(), 0)
        self.assertEqual(nQgis(), 1)
        # add layer to map
        mapDock.addLayers([TestObjects.createRasterLayer()])
        self.assertEqual(nSrc(), 1)
        self.assertEqual(nQgis(), 2)

        # unload
        E.removeSources()
        self.assertEqual(nSrc(), 0)
        self.assertEqual(nQgis(), 1)

        E.close()
        QgsProject.instance().removeAllMapLayers()

    def test_speclibDocks(self):
        EMB = EnMAPBox()
        EMB.loadExampleData()
        mapDock = EMB.createDock('MAP')
        self.assertIsInstance(mapDock, MapDock)
        sources = EMB.dataSources('RASTER')

        self.assertIsInstance(sources, list)
        self.assertTrue(len(sources) > 0)
        layers = [QgsRasterLayer(p) for p in sources]
        self.assertTrue(len(layers) > 0)
        mapDock.mapCanvas().setLayers(layers)

        speclibDock = EMB.createDock('SPECLIB')
        self.assertIsInstance(speclibDock, SpectralLibraryDock)
        slw = speclibDock.speclibWidget()
        self.assertIsInstance(slw, SpectralLibraryWidget)
        self.showGui(EMB.ui)
        EMB.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
