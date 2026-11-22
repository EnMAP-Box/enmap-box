import unittest

from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsVectorLayer, QgsProject, QgsRasterLayer

from enmapbox import initAll
from enmapbox.gui.dataviews.dockmanager import (
    MapDockTreeNode, SpeclibDockTreeNode, DockManager, DockManagerTreeModel,
    DockTreeView
)
from enmapbox.gui.dataviews.docks import DockArea
from enmapbox.gui.dataviews.mapdock import MapDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.speclib.core import is_spectral_library
from enmapbox.testing import start_app, TestCase, TestObjects

start_app()
initAll()


class MapDockTestCases(TestCase):

    def test_MapDock(self):
        da = DockArea()

        dock = MapDock()
        self.assertIsInstance(dock, MapDock)
        da.addDock(dock)
        self.showGui(da)

    def test_MapDockLayerHandling(self):
        EMB = EnMAPBox(load_other_apps=False, load_core_apps=False)
        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())

        EMB.createNewMapCanvas('Canvas1')
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
        from enmapboxtestdata import enmap, hires
        dock: MapDock = enmapBox.onDataDropped([QgsRasterLayer(enmap, 'enmap')])
        dock.insertLayer(0, QgsRasterLayer(hires, 'hires'))

        self.showGui(enmapBox.ui)
        enmapBox.close()
        QApplication.processEvents()
        QgsProject.instance().removeAllMapLayers()

    def test_canvasBridge(self):
        project = QgsProject()
        lyr1 = TestObjects.createVectorLayer()
        lyr1.setName('Layer 1')
        lyr2 = TestObjects.createVectorLayer()
        lyr2.setName('Layer 2')
        layers = [lyr1, lyr2]
        project.addMapLayers(layers)
        widgets = []

        manager = DockManager()
        dockArea = DockArea()
        manager.connectDockArea(dockArea)

        model = DockManagerTreeModel(manager)
        model.setProject(project)
        dock1 = manager.createDock('MAP', name='Tree1')
        dock2 = manager.createDock('MAP', name='Tree2')
        widgets.extend([dock1, dock2])
        root = model.rootGroup().children()[0]

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


if __name__ == '__main__':
    unittest.main()
