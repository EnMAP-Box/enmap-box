from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import enmap
from qgis.core import QgsRasterLayer
from qgis.gui import QgsDockWidget
from spectralindexexplorerapp import SpectralIndexExplorerDockWidget

qgsApp = start_app()
initAll()


class TestSpectralIndexExplorerDockWidget(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(enmap, 'enmap_berlin')
        enmapBox.onDataDropped([layer])

        for widget in enmapBox.ui.findChildren(QgsDockWidget):
            if isinstance(widget, SpectralIndexExplorerDockWidget):
                break

        self.assertIsInstance(widget, SpectralIndexExplorerDockWidget)
        widget.show()
        widget.mLayer.setLayer(layer)
        widget.mEditLayerName.setText('ndvi')
        widget.mEditFormula.setText('(N - R)/(N + R)')
        widget.apply()

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
