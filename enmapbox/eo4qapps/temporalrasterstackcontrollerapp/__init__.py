from typing import Optional

from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.typeguard import typechecked
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from geetimeseriesexplorerapp import GeeTimeseriesExplorerDockWidget
from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsTemporalNavigationObject, QgsDateTimeRange, QgsProject, QgsRasterLayer, \
    QgsSingleBandGrayRenderer, QgsSingleBandPseudoColorRenderer, Qgis, QgsRasterLayerTemporalProperties, \
    QgsPalettedRasterRenderer
from qgis.gui import QgsMapCanvas


def enmapboxApplicationFactory(enmapBox: EnMAPBox):
    return [TemporalRasterStackControllerApp(enmapBox)]


@typechecked
class TemporalRasterStackControllerApp(EnMAPBoxApplication):

    def __init__(self, enmapBox: Optional[EnMAPBox], parent=None
                 ):
        super().__init__(enmapBox, parent=parent)

        self.name = TemporalRasterStackControllerApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

        if enmapBox is not None:
            return  # we don't integrate into EnMAP-Box GUI!

        self.initQgisGui()

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/mIconTemporalRaster.svg')

    def initQgisGui(self):
        from qgis.utils import iface

        # add toolbar button
        self.actionToolbarIcon = QAction(self.icon(), 'Temporal Raster Stack Controller')
        self.actionToolbarIcon.triggered.connect(self.onToolbarIconClicked)
        iface.addToolBarIcon(self.actionToolbarIcon)
        self.temporalController: QgsTemporalNavigationObject = iface.mapCanvas().temporalController()
        self.temporalController.updateTemporalRange.connect(self.onUpdateTemporalRange)
        self.mapCanvas: QgsMapCanvas = iface.mapCanvas()

    def onToolbarIconClicked(self):
        from qgis.utils import iface

        layer = iface.activeLayer()
        if layer is None:
            return
        if layer.dataProvider().name() != 'gdal':
            return

        if layer.temporalProperties().isActive():
            layer.temporalProperties().setIsActive(False)
        else:
            begin = QDateTime(9999, 1, 1, 0, 0)
            end = QDateTime(1, 1, 1, 0, 0)
            layer.temporalProperties().setIsActive(True)
            layer.temporalProperties().setMode(Qgis.RasterTemporalMode.TemporalRangeFromDataProvider)
            try:
                begin = min(begin, RasterReader(layer).centerTime(1))
                end = max(end, RasterReader(layer).centerTime(layer.bandCount()))
            except Exception:
                pass
            self.temporalController.setTemporalExtents(QgsDateTimeRange(begin, end, True, True))

    def onUpdateTemporalRange(self, dateTimeRange: QgsDateTimeRange):

        startTime = dateTimeRange.begin()
        endTime = dateTimeRange.end()
        msecs = startTime.msecsTo(endTime)
        centerTime = startTime.addMSecs(int(msecs / 2))

        # handle GDAL raster layer
        layer: QgsRasterLayer
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsRasterLayer):
                continue
            temporalProperties: QgsRasterLayerTemporalProperties = layer.temporalProperties()
            if not temporalProperties.isActive():
                continue
            if temporalProperties.mode() != Qgis.RasterTemporalMode.TemporalRangeFromDataProvider:
                continue

            reader = RasterReader(layer)
            bandNo = reader.findTime(centerTime)
            if bandNo is None:
                return

            renderer = layer.renderer()
            if isinstance(renderer, QgsSingleBandGrayRenderer):
                renderer.setInputBand(bandNo)
            elif isinstance(renderer, QgsSingleBandPseudoColorRenderer):
                renderer.setBand(bandNo)
            elif isinstance(renderer, QgsPalettedRasterRenderer):
                categories = Utils.categoriesFromPalettedRasterRenderer(renderer)
                renderer = Utils.palettedRasterRendererFromCategories(layer.dataProvider(), bandNo, categories)
                layer.setRenderer(renderer)
            else:
                raise NotImplementedError(renderer.__class__)

            layer.rendererChanged.emit()
            layer.triggerRepaint()

        # handle EE raster layer
        geeTimeseriesExplorerDockWidget = GeeTimeseriesExplorerDockWidget.qgisInstance()
        if geeTimeseriesExplorerDockWidget.mUnderTemporalControl.isChecked():
            geeTimeseriesExplorerDockWidget.mCompositeDateStart.setDateTime(startTime)
            geeTimeseriesExplorerDockWidget.mCompositeDateEnd.setDateTime(endTime)
            GeeTimeseriesExplorerDockWidget.qgisInstance().onUpdateLayerClicked()
