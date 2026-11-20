from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsRasterLayer

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from sensorproductimportapp import SensorProductImportDockWidget

qgsApp = start_app()
initAll()


class TestSensorProductImportApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget in enmapBox.ui.findChildren(QDockWidget):
            if isinstance(widget, SensorProductImportDockWidget):
                break

        self.assertIsInstance(widget, SensorProductImportDockWidget)
        widget.show()

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()
