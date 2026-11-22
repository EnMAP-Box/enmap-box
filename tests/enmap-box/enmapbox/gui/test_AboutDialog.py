import unittest

from qgis.PyQt.QtWidgets import QApplication

from enmapbox import initAll
from enmapbox.gui.about import AboutDialog
from enmapbox.qgispluginsupport.qps.resources import ResourceBrowser
from enmapbox.testing import EnMAPBoxTestCase, start_app

start_app()
initAll()


class TestCasesAboutDialog(EnMAPBoxTestCase):

    def test_AboutDialog(self):
        d = AboutDialog()
        self.assertIsInstance(d, AboutDialog)
        self.showGui(d)
        QApplication.processEvents()

    def test_show_resources(self):
        b = ResourceBrowser()
        self.showGui(b)


if __name__ == '__main__':
    unittest.main()
