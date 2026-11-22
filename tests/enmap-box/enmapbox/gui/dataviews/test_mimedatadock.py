import unittest

from qgis.core import QgsProject

from enmapbox import initAll
from enmapbox.gui.dataviews.docks import DockArea
from enmapbox.gui.dataviews.mimedatadock import MimeDataDock
from enmapbox.testing import start_app, TestCase

start_app()
initAll()


class MimeDataDockTestCases(TestCase):

    def test_MimeDataDock(self):
        da = DockArea()
        dock = MimeDataDock()
        da.addDock(dock)
        self.showGui(da)

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main()
