from classificationstatisticsapp.classificationstatisticsdialog import ClassificationStatisticsDialog
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.typeguard import typechecked
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu


def enmapboxApplicationFactory(enmapBox):
    return [ClassificationStatisticsApp(enmapBox)]


@typechecked
class ClassificationStatisticsApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = ClassificationStatisticsApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/histogram.svg')

    @classmethod
    def title(cls):
        return 'Classification Statistics'

    def menu(self, appMenu: QMenu):
        for menu in [self.enmapbox.ui.menuToolsRasterStatistics, self.enmapbox.ui.menuToolsRasterVisualizations]:
            a = self.utilsAddActionInAlphanumericOrder(menu, self.title())
            a.triggered.connect(self.startGUI)
        return appMenu

    def startGUI(self):
        w = ClassificationStatisticsDialog(parent=self.enmapbox.ui)
        w.show()
