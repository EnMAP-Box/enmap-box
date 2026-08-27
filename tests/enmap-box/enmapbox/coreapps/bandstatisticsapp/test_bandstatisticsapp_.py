from qgis.core import QgsRasterLayer

from bandstatisticsapp import BandStatisticsDialog
from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap

qgsApp = start_app()
initAll()


class TestBandStatisticsApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
        enmapBox.onDataDropped([layer])

        widget = BandStatisticsDialog()
        widget.show()
        widget.mLayer.setLayer(layer)
        widget.onAddRendererBandsClicked()

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()
        # if False:
        #    qgsApp.exec()

        # self.dispose_widget(widget)
        # self.dispose_widget(enmapBox.ui)
