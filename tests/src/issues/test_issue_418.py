"""
This is a template to create an EnMAP-Box test
"""
import pathlib
import unittest

from enmapbox.gui.datasources.datasources import RasterDataSource
from enmapbox.gui.datasources.manager import DataSourceFactory
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase
from qgis.core import QgsProject

path = pathlib.Path(r'/home/benni/Downloads/MOD05_L2.A2022305.0005.061.2022335032530.hdf').resolve()


@unittest.skipIf(not path.is_file(), 'MODIS file does not exist')
class TestCaseIssue418(EnMAPBoxTestCase):

    def test_issue418(self):
        # this example shows you the standard environment of an EnMAPBoxTestCase

        # QGIS is up and running
        sources = DataSourceFactory.create(path, show_dialogs=False)
        source: RasterDataSource = [s for s in sources if 'mod05:Water_Vapor_Near_Infrared' in s.source()][0]
        enmapBox = EnMAPBox(load_core_apps=True, load_other_apps=False)
        enmapBox.addSource(source)
        mapDock = enmapBox.createMapDock('')
        layer = source.asMapLayer(enmapBox.project())

        mapDock.addLayers([layer])
        self.showGui(enmapBox.ui)
        s = ""
        enmapBox.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
