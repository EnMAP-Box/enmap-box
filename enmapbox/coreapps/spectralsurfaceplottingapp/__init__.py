import importlib.util

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu

from enmapbox.gui.applications import EnMAPBoxApplication

has_pyvista = importlib.util.find_spec('pyvista') is not None


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

        if not has_pyvista:
            a.setEnabled(False)
            a.setToolTip('Requires to install pyvista')

    def startGUI(self):
        if has_pyvista:
            from spectralsurfaceplottingapp.spectralsurfaceplottingwindow import SpectralSurfacePlottingWindow
            w = SpectralSurfacePlottingWindow(parent=self.enmapbox.ui)
            w.show()
