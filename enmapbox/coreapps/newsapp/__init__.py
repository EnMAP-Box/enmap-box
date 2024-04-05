from enmapbox.enmapboxsettings import enmapboxSettings, EnMAPBoxSettings
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.typeguard import typechecked
from newsapp.newsdockwidget import NewsDockWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon


def enmapboxApplicationFactory(enmapBox: EnMAPBox):
    return [NewsApp(enmapBox)]


@typechecked
class NewsApp(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = NewsApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

        self.initGui()

    @classmethod
    def icon(cls):
        return QIcon()

    def initGui(self):
        # add main dock and toolbar button
        self.dock = NewsDockWidget(parent=self.parent())
        self.enmapbox.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.setWindowIcon(self.icon())

        if EnMAPBoxSettings().value(EnMAPBoxSettings.SHOW_NEWS_PANEL, type=bool):
            self.dock.show()
        else:
            self.dock.hide()

        self.dock.addItems()
