from qgis.core import QgsRasterLayer

from colorspaceexplorerapp import ColorSpaceExplorerDialog
from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap

qgsApp = start_app()
initAll()


class TestColorSpaceExplorerApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        layer = QgsRasterLayer(enmap, 'enmap_berlin.bsq')
        enmapBox.onDataDropped([layer])

        widget = ColorSpaceExplorerDialog()
        widget.show()
        widget.mLayer.setLayer(layer)

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()
