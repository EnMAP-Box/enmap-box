import pathlib
import site
import unittest

from enmapbox import DIR_ENMAPBOX
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt.QtWidgets import QWidget

site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'coreapps')

try:
    from vrtbuilderapp import vrtBuilderPluginInstalled, VRTBuilderApp
except ModuleNotFoundError as ex:
    unittest.skip(f'Module not found: {ex}')


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
