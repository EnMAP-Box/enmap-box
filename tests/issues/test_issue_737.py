"""
Addresses issue 737
"""
import unittest

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.core import QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsLayerTreeLayer
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer, QgsVectorLayer

start_app()


class TestIssue737(EnMAPBoxTestCase):

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'Unknown fail in conda CI')
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
        speclib.setRenderer(r1.clone())

        model = emb.dockManagerTreeModel()
        l1 = model.findLayerTreeLayers(speclib)
        l2 = model.findLayerTreeLayers(speclib.id())
        self.assertEqual(len(l1), 2)
        self.assertListEqual(l1, l2)
        node = model.rootGroup()

        layerNodes = [n for n in node.findLayers() if n.layerId() == speclib.id()]
        for n in layerNodes:
            self.assertIsInstance(n, QgsLayerTreeLayer)
            lyr = n.layer()
            r = lyr.renderer()
            s = r.symbol()
            self.assertEqual(s.color(), speclib.renderer().symbol().color())

        self.showGui(emb.ui)
        emb.close()

        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
