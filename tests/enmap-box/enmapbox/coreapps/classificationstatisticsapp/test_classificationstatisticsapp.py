from qgis.core import QgsRasterLayer

from classificationstatisticsapp import ClassificationStatisticsDialog
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import start_app
from enmapboxprocessing.testcase import TestCase
from enmapboxtestdata import landcover_map_l3

qgsApp = start_app()
start_app()


class TestClassificationStatisticsApp(TestCase):

    def test(self):
        enmapBox = EnMAPBox()
        layer = QgsRasterLayer(landcover_map_l3, 'landcover_map_l3')
        enmapBox.onDataDropped([layer])

        widget = ClassificationStatisticsDialog()
        widget.show()
        widget.mLayer.setLayer(layer)

        self.showGui([enmapBox.ui, widget])
        enmapBox.close()

        # if False:
        #    qgsApp.exec()

        # self.dispose_widget(widget)
        # self.dispose_widget(enmapBox.ui)
