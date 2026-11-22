from qgis.core import QgsRasterLayer

from enhancedmultibandcolorapp import EnhancedMultiBandColorDialog
from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap

qgsApp = start_app()
initAll()


class TestEnhancedMultiBandColorApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        widget = EnhancedMultiBandColorDialog()
        widget.show()
        widget.mLayer.setLayer(layer)

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()
