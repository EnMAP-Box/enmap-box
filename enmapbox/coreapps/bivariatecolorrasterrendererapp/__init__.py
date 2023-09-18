from bivariatecolorrasterrendererapp.bivariatecolorrasterrendererdialog import BivariateColorRasterRendererDialog
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction
from enmapbox.typeguard import typechecked


def enmapboxApplicationFactory(enmapBox):
    return [BivariateColorRasterRendererApp(enmapBox)]


@typechecked
class BivariateColorRasterRendererApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = BivariateColorRasterRendererApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/propertyicons/symbology.svg')

    @classmethod
    def title(cls):
        return 'Bivariate Color Raster Renderer'

    def menu(self, appMenu: QMenu):
        a = self.utilsAddActionInAlphanumericOrder(self.enmapbox.ui.menuToolsRasterVisualizations, self.title())
        assert isinstance(a, QAction)
        a.triggered.connect(self.startGUI)

    def startGUI(self):
        w = BivariateColorRasterRendererDialog(parent=self.enmapbox.ui)
        w.show()
