from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsRasterLayer

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from rasterbandstackingapp import RasterBandStackingDockWidget

qgsApp = start_app()
initAll()


class TestRasterBandStackingApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget in enmapBox.ui.findChildren(QDockWidget):
            if isinstance(widget, RasterBandStackingDockWidget):
                break

        self.assertIsInstance(widget, RasterBandStackingDockWidget)

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()
