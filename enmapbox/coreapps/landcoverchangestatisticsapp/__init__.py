from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.typeguard import typechecked
from landcoverchangestatisticsapp.landcoverchangestatisticsmainwindow import LandCoverChangeStatisticsMainWindow

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu


def enmapboxApplicationFactory(enmapBox):
    return [LandCoverChangeStatisticsApp(enmapBox)]


@typechecked
class LandCoverChangeStatisticsApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = LandCoverChangeStatisticsApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/histogram.svg')

    @classmethod
    def title(cls):
        return 'Land Cover Change Statistics'

    def menu(self, appMenu: QMenu):
        a = self.utilsAddActionInAlphanumericOrder(self.enmapbox.ui.menuApplicationsClassification, self.title())
        a.triggered.connect(self.startGUI)

    def startGUI(self):
        w = LandCoverChangeStatisticsMainWindow(parent=self.enmapbox.ui)
        w.show()
