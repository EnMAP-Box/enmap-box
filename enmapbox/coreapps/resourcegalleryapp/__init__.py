from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction

from bandstatisticsapp.bandstatisticsdialog import BandStatisticsDialog
from enmapbox.gui.applications import EnMAPBoxApplication
from typeguard import typechecked


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
        return QIcon()

    @classmethod
    def title(cls):
        return 'Resource Gallery'

    def startGUI(self):
        w = BandStatisticsDialog(parent=self.enmapbox.ui)
        w.show()
