from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction
from rastersourcebandpropertieseditorapp.rastersourcebandpropertieseditordialog import \
    RasterSourceBandPropertiesEditorDialog
from typeguard import typechecked


def enmapboxApplicationFactory(enmapBox):
    return [RasterSourceBandPropertiesEditorApp(enmapBox)]


@typechecked
class RasterSourceBandPropertiesEditorApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = RasterSourceBandPropertiesEditorApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/enmapbox/gui/ui/icons/metadata.svg')

    @classmethod
    def title(cls):
        return 'Raster Source Band Properties Editor'

    def menu(self, appMenu: QMenu):
        appMenu: QMenu = self.enmapbox.menu('Tools')
        a = self.utilsAddActionInAlphanumericOrder(appMenu, self.title())
        assert isinstance(a, QAction)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return appMenu

    def startGUI(self):
        w = RasterSourceBandPropertiesEditorDialog(parent=self.enmapbox.ui)
        w.show()
