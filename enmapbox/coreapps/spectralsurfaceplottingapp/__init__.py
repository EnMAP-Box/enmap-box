from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu
from spectralsurfaceplottingapp.spectralsurfaceplottingwindow import SpectralSurfacePlottingWindow


def enmapboxApplicationFactory(enmapBox):
    return [SpectralSurfacePlottingApp(enmapBox)]


class SpectralSurfacePlottingApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = SpectralSurfacePlottingApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/mLayoutItem3DMap.svg')

    @classmethod
    def title(cls):
        return 'Spectral Surface Plotting'

    def menu(self, appMenu: QMenu):
        a = self.utilsAddActionInAlphanumericOrder(self.enmapbox.ui.menuTools, self.title())
        a.triggered.connect(self.startGUI)

    def startGUI(self):
        w = SpectralSurfacePlottingWindow(parent=self.enmapbox.ui)
        w.show()
