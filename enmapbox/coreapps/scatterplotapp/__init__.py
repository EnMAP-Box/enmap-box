from os.path import dirname, join

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction


from enmapbox.gui.applications import EnMAPBoxApplication
from scatterplotapp.scatterplotdialog import ScatterPlotDialog
from typeguard import typechecked


def enmapboxApplicationFactory(enmapBox):
    return [ScatterPlotApp(enmapBox)]


@typechecked
class ScatterPlotApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = ScatterPlotApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(join(dirname(__file__), 'scatterplotdialog.svg'))

    @classmethod
    def title(cls):
        return 'Scatter Plot'

    def menu(self, appMenu: QMenu):
        appMenu: QMenu = self.enmapbox.menu('Tools')
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Scatter Plot')
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def startGUI(self):
        w = ScatterPlotDialog(parent=self.enmapbox.ui)
        w.show()
