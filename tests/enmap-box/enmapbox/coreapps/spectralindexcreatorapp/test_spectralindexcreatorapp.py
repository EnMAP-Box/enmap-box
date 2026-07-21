from colorspaceexplorerapp import ColorSpaceExplorerDialog
from decorrelationstretchapp import DecorrelationStretchDialog
from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from qgis.core import QgsRasterLayer
from spectralindexcreatorapp import SpectralIndexCreatorDialog

qgsApp = start_app()
initAll()


class TestDecorrelationStretchApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        widget: SpectralIndexCreatorDialog = SpectralIndexCreatorDialog()
        widget.show()
        widget.mLayer.setLayer(layer)

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
