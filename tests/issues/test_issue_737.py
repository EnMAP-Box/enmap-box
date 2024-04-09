"""
Addresses issue 737
"""
import unittest

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis._core import QgsMarkerSymbol, QgsSingleSymbolRenderer
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer, QgsVectorLayer

start_app()


class TestIssue737(EnMAPBoxTestCase):

    def test_issue_737(self):
        emb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        from enmapbox.exampledata import enmap, landcover_point

        lyr1 = QgsRasterLayer(enmap, 'enmap')
        lyr2 = QgsVectorLayer(landcover_point, 'landcover')

        mapDock = emb.createMapDock()
        slwDock = emb.createSpectralLibraryDock()
        speclib = slwDock.speclib()
        mapDock.addLayers([lyr1, speclib])

        symbolRed = QgsMarkerSymbol.createSimple({'name': 'square', 'color': 'red'})
        symbolOrange = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'orange'})
        r1 = QgsSingleSymbolRenderer(QgsMarkerSymbol(symbolRed))
        r2 = QgsSingleSymbolRenderer(QgsMarkerSymbol(symbolOrange))
        speclib.setRenderer(r1)

        model = emb.dockManagerTreeModel()
        node = model.rootGroup()
        lyrIds = node.findLayerIds()

        self.showGui(emb.ui)
        emb.close()

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
