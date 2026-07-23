from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from profileanalyticsapp import ProfileAnalyticsDockWidget
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()


class TestProfileAnalyticsDockWidget(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget in enmapBox.ui.findChildren(QDockWidget):
            if isinstance(widget, ProfileAnalyticsDockWidget):
                break

        self.assertIsInstance(widget, ProfileAnalyticsDockWidget)
        widget.show()

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
