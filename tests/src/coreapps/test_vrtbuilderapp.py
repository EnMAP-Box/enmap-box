import pathlib
import site
import unittest

from qgis.PyQt.QtWidgets import QWidget
from enmapbox import DIR_ENMAPBOX
from enmapbox.testing import TestObjects, EnMAPBoxTestCase
from qgis.core import QgsRasterLayer, QgsPalettedRasterRenderer, QgsProject

site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'coreapps')

from vrtbuilderapp import vrtBuilderPluginInstalled, VRTBuilderApp

from enmapbox import EnMAPBox, EnMAPBoxApplication


class TestVRTBuilderApp(EnMAPBoxTestCase):

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking dialogs')
    def test_startapp(self):

        enmapbox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        enmapbox.loadExampleData()

        APP = VRTBuilderApp(enmapbox)

        self.assertIsInstance(APP, EnMAPBoxApplication)
        w = APP.startGUI()
        if vrtBuilderPluginInstalled():
            self.assertIsInstance(w, QWidget)

            self.showGui([enmapbox, w])
        else:
            self.assertTrue(w is None)


if __name__ == "__main__":

    unittest.main(buffer=False)
