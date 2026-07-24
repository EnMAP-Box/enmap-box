from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from locationbrowserapp import LocationBrowserDockWidget
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()


class TestLocationBrowserDockWidget(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget in enmapBox.ui.findChildren(QDockWidget):
            if isinstance(widget, LocationBrowserDockWidget):
                break

        self.assertIsInstance(widget, LocationBrowserDockWidget)
        widget.show()
        widget.onRequestNominatimClicked()

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
