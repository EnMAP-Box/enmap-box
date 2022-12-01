"""
This is a template to create an EnMAP-Box test
"""
import unittest

from enmapbox import EnMAPBox
from enmapbox.gui.dataviews.dockmanager import MapDockTreeNode
from enmapbox.testing import EnMAPBoxTestCase
from enmapboxtestdata import enmap, hires
from qgis.core import QgsRasterLayer


class EnMAPBoxTestIssue88(EnMAPBoxTestCase):

    def test_issue88(self):
        # this example shows you the standard environment of an EnMAPBoxTestCase
        lyr1 = QgsRasterLayer(enmap, 'EnMAP')
        lyr2 = QgsRasterLayer(hires, 'HyMap')

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        tree1: MapDockTreeNode = enmapBox.createNewMapCanvas('Map 1').layerTree()
        tree2: MapDockTreeNode = enmapBox.createNewMapCanvas('Map 2').layerTree()

        tree1.addLayer(lyr1)

        self.showGui(enmapBox.ui)


if __name__ == '__main__':
    unittest.main(buffer=False)
