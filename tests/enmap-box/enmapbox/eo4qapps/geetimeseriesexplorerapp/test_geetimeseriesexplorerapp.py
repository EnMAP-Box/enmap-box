from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from geetimeseriesexplorerapp import GeeTimeseriesExplorerDockWidget, GeeTemporalProfileDockWidget
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()


class TestGeeTimeseriesExplorerApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget1 in enmapBox.ui.findChildren(QDockWidget):
            print(widget1)
            if isinstance(widget1, GeeTimeseriesExplorerDockWidget):
                break

        self.assertIsInstance(widget1, GeeTimeseriesExplorerDockWidget)
        widget1.show()

        for widget2 in enmapBox.ui.findChildren(QDockWidget):
            if isinstance(widget2, GeeTemporalProfileDockWidget):
                break

        self.assertIsInstance(widget2, GeeTemporalProfileDockWidget)
        widget2.show()

        if False:
            qgsApp.exec()

        self.dispose_widget(widget1)
        self.dispose_widget(widget2)
        self.dispose_widget(enmapBox.ui)
