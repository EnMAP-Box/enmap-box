from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from multisourcemultibandcolorrendererapp import MultiSourceMultiBandColorRendererDialog
from qgis.core import QgsRasterLayer

qgsApp = start_app()
initAll()


class TestMultiSourceMultiBandColorRendererDialog(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        widget = MultiSourceMultiBandColorRendererDialog()
        widget.mLayer1.setLayer(layer)
        widget.mLayer2.setLayer(layer)
        widget.mLayer3.setLayer(layer)
        widget.mBand1.setBand(62)
        widget.mBand2.setBand(39)
        widget.mBand3.setBand(21)
        widget.mMin1.setText('0')
        widget.mMin2.setText('0')
        widget.mMin3.setText('0')
        widget.mMax1.setText('1')
        widget.mMax2.setText('1')
        widget.mMax3.setText('1')
        widget.show()

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
