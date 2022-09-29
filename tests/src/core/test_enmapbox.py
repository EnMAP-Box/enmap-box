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

from qgis.PyQt.QtWidgets import QGridLayout, QWidget, QLabel

import qgis
from enmapbox import DIR_REPO
from enmapbox.gui.dataviews.docks import SpectralLibraryDock, MapDock, Dock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import SpectralProfile
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint
from enmapbox.testing import TestObjects, EnMAPBoxTestCase
from qgis.core import Qgis, QgsExpressionContextGenerator, QgsProcessingContext, QgsExpressionContext
from qgis.core import QgsProject, QgsMapLayer, QgsRasterLayer, QgsVectorLayer, \
    QgsLayerTree, QgsApplication
from qgis.gui import QgsMapLayerComboBox, QgisInterface, QgsProcessingContextGenerator, QgsMapCanvas


# mini test


class EnMAPBoxTests(EnMAPBoxTestCase):

    def tearDown(self):

        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox):
            emb.close()

        assert EnMAPBox.instance() is None

        QgsProject.instance().removeAllMapLayers()

        super().tearDown()

    def test_AboutDialog(self):

        from enmapbox.gui.about import AboutDialog
        d = AboutDialog()
        self.assertIsInstance(d, AboutDialog)
        self.showGui(d)

    @unittest.skipIf(not (pathlib.Path(DIR_REPO) / 'qgisresources').is_dir(), 'qgisresources dir does not exist')
    def test_find_qgis_resources(self):
        from enmapbox.qgispluginsupport.qps.resources import findQGISResourceFiles
        results = findQGISResourceFiles()
        print('QGIS Resource files:')
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

    def test_instance_pure(self):
        EMB = EnMAPBox(load_other_apps=False, load_core_apps=False)

        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())

        widgets = [qgis.utils.iface.mainWindow(), EMB.ui]

        if True:
            cbQGIS = QgsMapLayerComboBox()
            cbQGIS.setWindowTitle('QGIS Layers')
            widgets.append(cbQGIS)

            if Qgis.versionInt() > 32400:
                cbEMB = QgsMapLayerComboBox()
                cbEMB.setWindowTitle('EnMAP-Box Layers')
                cbEMB.setProject(EMB.project())
                widgets.append(cbEMB)

        self.showGui(widgets)

    def test_context_interfaces(self):

        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        self.assertIsInstance(EMB, QgsExpressionContextGenerator)
        self.assertIsInstance(EMB, QgsProcessingContextGenerator)
        EMB.loadExampleData()
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

    def test_instance_all_apps(self):
        EMB = EnMAPBox(load_core_apps=True, load_other_apps=True)
        self.assertIsInstance(EMB, EnMAPBox)
        self.showGui(EMB.ui)

    def test_instance_coreapps(self):
        EMB = EnMAPBox(load_core_apps=True, load_other_apps=False)
        self.assertIsInstance(EMB, EnMAPBox)
        self.showGui(EMB.ui)

    def test_instance_coreapps_and_data(self):

        EMB = EnMAPBox(load_core_apps=True, load_other_apps=False)

        self.assertTrue(len(QgsProject.instance().mapLayers()) == 0)
        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())

        EMB.openExampleData(mapWindows=1, testData=True)
        self.assertTrue(len(QgsProject.instance().mapLayers()) > 0)
        canvases = EMB.mapCanvases()
        self.assertTrue(canvases[-1] == EMB.currentMapCanvas())

        self.showGui([EMB.ui])

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
        self.assertTrue(lyrNew in list(QgsProject.instance().mapLayers().values()))
        self.assertTrue(lyrNew in list(box.project().mapLayers().values()))
        mapDock.removeLayer(lyrNew)
        self.assertFalse(lyrNew in list(QgsProject.instance().mapLayers().values()))
        self.assertFalse(lyrNew in list(box.project().mapLayers().values()))

        n2 = cb1.model().rowCount()
        self.assertEqual(n2, n - 1)

    def test_createDock(self):

        EMB = EnMAPBox()
        for d in ['MAP', 'TEXT', 'SPECLIB', 'MIME']:
            dock = EMB.createDock(d)
            self.assertIsInstance(dock, Dock)
        self.showGui()

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

        self.showGui()

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking dialogs')
    def test_createNewLayers(self):

        E = EnMAPBox(load_core_apps=False, load_other_apps=False)
        E.ui.mActionCreateNewMemoryLayer.trigger()

        E.ui.mActionCreateNewShapefileLayer.trigger()

        E.ui.mActionCreateNewGeoPackageLayer.trigger()

        self.showGui(E.ui)

    def test_loadExampleData(self):
        E = EnMAPBox(load_core_apps=False, load_other_apps=False)
        E.loadExampleData()
        n = len(E.dataSources())
        self.assertTrue(n > 0)
        self.showGui(E.ui)

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
        self.assertTrue(len(slw.speclib()) == 0)
        center = SpatialPoint.fromMapCanvasCenter(mapDock.mapCanvas())

        profiles = SpectralProfile.fromMapCanvas(mapDock.mapCanvas(), center)
        for p in profiles:
            self.assertIsInstance(p, SpectralProfile)


if __name__ == '__main__':
    unittest.main(buffer=False)
