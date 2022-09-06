from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction

from enmapbox.gui.applications import EnMAPBoxApplication
from spectralindexcreatorapp.spectralindexcreatordialog import SpectralIndexCreatorDialog
from typeguard import typechecked


def enmapboxApplicationFactory(enmapBox):
    return [SpectralIndexCreatorApp(enmapBox)]


@typechecked
class SpectralIndexCreatorApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = SpectralIndexCreatorApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def icon(self):
        return QIcon(None)

    def menu(self, appMenu: QMenu):
        a = self.utilsAddActionInAlphanumericOrder(appMenu, 'Spectral Index Creator')
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def startGUI(self, *args):
        w = SpectralIndexCreatorDialog(parent=self.enmapbox.ui)
        w.show()
