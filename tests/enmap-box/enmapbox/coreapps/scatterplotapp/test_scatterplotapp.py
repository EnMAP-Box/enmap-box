from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from qgis.core import QgsRasterLayer
from scatterplotapp import ScatterPlotDialog

qgsApp = start_app()
initAll()


class TestScatterPlotDialogApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        widget = ScatterPlotDialog()
        widget.show()
        widget.mLayerX.setLayer(layer)
        widget.mLayerY.setLayer(layer)
        widget.mBandX.setBand(1)
        widget.mBandY.setBand(100)

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
