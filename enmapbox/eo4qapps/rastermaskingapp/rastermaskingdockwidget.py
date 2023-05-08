from qgis.PyQt.QtWidgets import QTableWidget, QToolButton

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.typeguard import typechecked
from qgis.PyQt import uic
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsMapLayerComboBox, QgsDockWidget, QgisInterface


@typechecked
class RasterMaskingDockWidget(QgsDockWidget):
    mRaster: QgsMapLayerComboBox
    mThresholdingTable: QTableWidget
    mThresholdingAdd: QToolButton
    mThresholdingRemove: QToolButton
    mThresholdingRemoveAll: QToolButton

    EnmapBoxInterface, QgisInterface = 0, 1

    def __init__(self, parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        # set from outside
        self.interface = None
        self.interfaceType = None

        self.mRaster.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def enmapBoxInterface(self) -> EnMAPBox:
        return self.interface

    def qgisInterface(self):
        return self.interface

    def setInterface(self, interface):
        self.interface = interface
        if isinstance(interface, EnMAPBox):
            self.interfaceType = 0
        elif isinstance(interface, QgisInterface):
            self.interfaceType = 1
        else:
            raise ValueError()

    def onThresholdingAddClicked(self):

        self.mThresholdingTable.setRowCount(self.mThresholdingTable.rowCount() + 1)
        row = self.mRasterTable.rowCount() - 1
        mRaster = QgsMapLayerComboBox()
        mRaster.setFilters(QgsMapLayerProxyModel.RasterLayer)
        mRaster.setExcludedProviders(['wms'])
        mRaster.setAllowEmptyLayer(True)

        if self.interfaceType == self.EnmapBoxInterface:
            sources = self.enmapBoxInterface().dataSources('RASTER', True)
            mRaster.setAdditionalItems(sources)
        self.mRasterTable.setCellWidget(row, 0, mRaster)

        weiter

        mMultiBand = MultipleRasterBandSelectionWidget()

        mRaster.layerChanged.connect(self.onLayerChanged)
        mRaster.mMultiBand = mMultiBand
        self.mRasterTable.setCellWidget(row, 1, mMultiBand)

        if uri is not None:
            items = mRaster.additionalItems()
            if uri not in items:
                items.append(uri)
            mRaster.setAdditionalItems(items)
            mRaster.setCurrentText(uri)
            layer = QgsRasterLayer(uri)
            mMultiBand.setLayer(layer)
            mMultiBand.setCurrentBands(None)
        elif layer is not None:
            mRaster.setLayer(layer)
            mMultiBand.setLayer(layer)
            mMultiBand.setCurrentBands(None)
        else:
            mRaster.setLayer(None)
            mMultiBand.setLayer(None)

        if bandNo is not None:
            mMultiBand.mBand.setCurrentIndex(bandNo)

        # self.onLayerChanged()
