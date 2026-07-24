from classfractionstatisticsapp import ClassFractionStatisticsDialog
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import fraction_map_l3
from qgis.core import QgsRasterLayer

qgsApp = start_app()
start_app()


class TestClassFractionStatisticsApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox(None)
        layer = QgsRasterLayer(fraction_map_l3, 'fraction_map_l3')
        enmapBox.onDataDropped([layer])

        widget = ClassFractionStatisticsDialog()
        widget.show()
        widget.mLayer.setLayer(layer)

        if False:
            qgsApp.exec()

        self.dispose_widget(widget)
        self.dispose_widget(enmapBox.ui)
