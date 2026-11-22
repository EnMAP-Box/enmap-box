import unittest

from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout
from qgis.core import QgsProject
from qgis.gui import QgsLayerTreeView

from enmapbox import initAll
from enmapbox.gui.datasources.manager import DataSourceManager
from enmapbox.gui.dataviews.dockmanager import DockTreeView, DockManager, DockManagerTreeModel, SpeclibDockTreeNode, \
    createDockTreeNode
from enmapbox.gui.dataviews.docks import DockArea
from enmapbox.gui.dataviews.mimedatadock import MimeDataDock
from enmapbox.gui.dataviews.spectrallibrarydock import SpectralLibraryDock
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from enmapbox.testing import start_app, TestCase, TestObjects

start_app()
initAll()


class SpectralLibraryDockTestCases(TestCase):

    def test_MimeDataDock(self):
        da = DockArea()
        dock = MimeDataDock()
        da.addDock(dock)
        self.showGui(da)

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

        model.findDockNode(speclibDock)
        model.findDockNode(speclibDock.speclibWidget())

        w = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(TV)
        layout.addWidget(dockArea)
        w.setLayout(layout)
        self.showGui(w)
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

    def test_SpeclibDockTreeNode(self):
        TestObjects.createSpectralLibrary(name='speclib1')
        TestObjects.createSpectralLibrary(name='speclib2')

        dock = SpectralLibraryDock()
        node = createDockTreeNode(dock)
        self.assertIsInstance(node, SpeclibDockTreeNode)
        slw = node.speclibWidget()
        slw.plotModel()
        self.assertIsInstance(slw, SpectralLibraryWidget)


if __name__ == '__main__':
    unittest.main()
