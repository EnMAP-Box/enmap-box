from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction

from classfractionstatisticsapp.classfractionstatisticsdialog import ClassFractionStatisticsDialog
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.typeguard import typechecked


def enmapboxApplicationFactory(enmapBox):
    return [ClassFractionStatisticsApp(enmapBox)]


@typechecked
class ClassFractionStatisticsApp(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = ClassFractionStatisticsApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/propertyicons/symbology.svg')

    @classmethod
    def title(cls):
        return 'Class Fraction/Probability Renderer and Statistics'

    def menu(self, appMenu: QMenu):
        for menu in [self.enmapbox.ui.menuToolsRasterStatistics, self.enmapbox.ui.menuToolsRasterVisualizations]:
            a = self.utilsAddActionInAlphanumericOrder(menu, self.title())
            a.triggered.connect(self.startGUI)

    def startGUI(self):
        w = ClassFractionStatisticsDialog(parent=self.enmapbox.ui)
        w.show()
