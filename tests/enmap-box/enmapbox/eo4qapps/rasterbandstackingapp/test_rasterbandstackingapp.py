from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsRasterLayer
from rasterbandstackingapp import RasterBandStackingDockWidget

qgsApp = start_app()
initAll()


class TestRasterBandStackingApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget in enmapBox.ui.findChildren(QDockWidget):
            if isinstance(widget, RasterBandStackingDockWidget):
                break

        self.assertIsInstance(widget, RasterBandStackingDockWidget)
        widget.show()

        if not False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
