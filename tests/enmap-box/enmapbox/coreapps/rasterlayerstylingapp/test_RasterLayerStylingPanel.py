from qgis.gui import QgsDockWidget

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from qgis.core import QgsRasterLayer
from rasterlayerstylingapp import RasterLayerStylingPanel

qgsApp = start_app()
initAll()


class TestRasterLayerStylingPanel(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget in enmapBox.ui.findChildren(QgsDockWidget):
            if isinstance(widget, RasterLayerStylingPanel):
                break

        self.assertIsInstance(widget, RasterLayerStylingPanel)
        widget.show()

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
