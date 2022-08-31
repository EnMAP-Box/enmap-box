from qgis.core import QgsRasterLayer

from enmapbox.exampledata import enmap
from enmapbox.gui.widgets.multiplemaplayerselectionwidget import MultipleMapLayerSelectionWidget
from enmapbox.testing import EnMAPBoxTestCase


class TestMultipleMapLayerSelectionWidget(EnMAPBoxTestCase):

    def test(self):
        from enmapbox import EnMAPBox, initAll

        from enmapbox.testing import start_app

        qgsApp = start_app()

        initAll()
        enmapBox = EnMAPBox(None)
        enmapBox.ui.hide()
        layer = QgsRasterLayer(enmap)
        enmapBox.onDataDropped([layer])
        w = MultipleMapLayerSelectionWidget()
        w.setCurrentLayers([layer])
        self.assertListEqual([layer], w.currentLayers())

        # nothing really to test here, becausde the whole purpose of the widget is code highlighting
