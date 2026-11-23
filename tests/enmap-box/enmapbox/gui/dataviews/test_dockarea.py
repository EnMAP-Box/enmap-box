import unittest

# from pyqtgraph.dockarea import Dock
from pyqtgraph.dockarea import DockArea as pDockArea, Dock as pDock
from qgis.PyQt.QtWidgets import QMainWindow

from enmapbox.gui.dataviews.dockarea import DockArea as eDockArea
from enmapbox.gui.dataviews.docks import Dock
from enmapbox.testing import TestCase, start_app

start_app()


# from pyqtgraph.dockarea.DockArea import pDockArea


class DockAreaTestCases(TestCase):

    def test_dockarea(self):
        use_enmapbox_dock = True
        if not use_enmapbox_dock:
            da = pDockArea()
            dock1 = pDock('pDock1')
            dock2 = pDock('pDock2')

        else:
            dock1 = Dock('Dock1')
            dock2 = Dock('Dock2')
            da = eDockArea()
        dw = QMainWindow()
        dw.setCentralWidget(da)
        dw.resize(800, 600)
        da.addDock(dock1)
        da.addDock(dock2)
        self.showGui(dw)


if __name__ == '__main__':
    unittest.main()
