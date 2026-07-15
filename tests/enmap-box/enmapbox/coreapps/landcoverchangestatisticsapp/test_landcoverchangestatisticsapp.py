from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from landcoverchangestatisticsapp import LandCoverChangeStatisticsMainWindow
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()


class TestHsvColorRasterRendererApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        widget = LandCoverChangeStatisticsMainWindow()
        widget.show()

        if not False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
