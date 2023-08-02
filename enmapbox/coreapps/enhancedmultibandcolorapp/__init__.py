from enhancedmultibandcolorapp.enhancedmultibandcolordialog import EnhancedMultiBandColorDialog
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.typeguard import typechecked
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu


def enmapboxApplicationFactory(enmapBox):
    return [EnhancedMultiBandColorApp(enmapBox)]


@typechecked
class EnhancedMultiBandColorApp(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = EnhancedMultiBandColorApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/propertyicons/symbology.svg')

    @classmethod
    def title(cls):
        return 'Enhanced Multiband Color Renderer'

    def menu(self, appMenu: QMenu):
        a = self.utilsAddActionInAlphanumericOrder(self.enmapbox.ui.menuToolsRasterVisualizations, self.title())
        a.triggered.connect(self.startGUI)

    def startGUI(self):
        w = EnhancedMultiBandColorDialog(parent=self.enmapbox.ui)
        w.show()
