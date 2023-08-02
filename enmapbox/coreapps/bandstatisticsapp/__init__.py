from bandstatisticsapp.bandstatisticsdialog import BandStatisticsDialog
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction
from enmapbox.typeguard import typechecked


def enmapboxApplicationFactory(enmapBox):
    return [BandStatisticsApp(enmapBox)]


@typechecked
class BandStatisticsApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = BandStatisticsApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/histogram.svg')

    @classmethod
    def title(cls):
        return 'Band Statistics'

    def menu(self, appMenu: QMenu):
        a = self.utilsAddActionInAlphanumericOrder(self.enmapbox.ui.menuToolsRasterStatistics, self.title())
        a.triggered.connect(self.startGUI)

    def startGUI(self):
        w = BandStatisticsDialog(parent=self.enmapbox.ui)
        w.show()
