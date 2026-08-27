from qgis.core import QgsRasterLayer

from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from hsvcolorrasterrendererapp import HsvColorRasterRendererDialog

qgsApp = start_app()
initAll()


class TestHsvColorRasterRendererApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        widget = HsvColorRasterRendererDialog()
        widget.show()
        widget.mLayer.setLayer(layer)

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()
