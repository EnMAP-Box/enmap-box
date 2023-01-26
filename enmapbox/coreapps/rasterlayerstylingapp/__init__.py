from typing import Optional

from qgis.PyQt.QtCore import Qt

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.applications import EnMAPBoxApplication
from typeguard import typechecked
from rasterlayerstylingapp.rasterlayerstylingpanel import RasterLayerStylingPanel


def enmapboxApplicationFactory(enmapBox: EnMAPBox):
    return [RasterLayerStylingApp(enmapBox)]


@typechecked
class RasterLayerStylingApp(EnMAPBoxApplication):

    _panel = None

    def __init__(self, enmapBox: EnMAPBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = RasterLayerStylingApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

        self.initGui()

    def initGui(self):
        RasterLayerStylingApp._panel = RasterLayerStylingPanel(self.enmapbox, self.enmapbox.ui)
        self.enmapbox.addPanel(Qt.RightDockWidgetArea, self._panel, False)

    @classmethod
    def panel(cls) -> Optional[RasterLayerStylingPanel]:
        return cls._panel
