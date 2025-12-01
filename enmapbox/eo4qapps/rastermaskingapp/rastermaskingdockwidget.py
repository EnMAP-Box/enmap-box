from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QTableWidget, QToolButton, QComboBox, QLineEdit, QDockWidget
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsMapLayerComboBox, QgsRasterBandComboBox, QgisInterface

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.typeguard import typechecked


@typechecked
class RasterMaskingDockWidget(QDockWidget):
    mRaster: QgsMapLayerComboBox
    mThresholdingTable: QTableWidget
    mThresholdingAdd: QToolButton
    mThresholdingRemove: QToolButton
    mThresholdingRemoveAll: QToolButton
    mApply: QToolButton

    EnmapBoxInterface, QgisInterface = 0, 1

    def __init__(self, parent=None):
        QDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        # set from outside
        self.interface = None
        self.interfaceType = None

        self.mRaster.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mThresholdingAdd.clicked.connect(self.onThresholdingAddClicked)
        self.mThresholdingRemove.clicked.connect(self.onThresholdingRemoveClicked)
        self.mThresholdingRemoveAll.clicked.connect(self.onThresholdingRemoveAllClicked)
        self.mApply.clicked.connect(self.onApplyClicked)

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

    operators = ['less than', 'less than or equals', 'greater than', 'greater than or equals', 'equals', 'not equals']

    def onThresholdingAddClicked(self):

        self.mThresholdingTable.setRowCount(self.mThresholdingTable.rowCount() + 1)
        row = self.mThresholdingTable.rowCount() - 1

        mRaster = QgsMapLayerComboBox()
        mRaster.setFilters(QgsMapLayerProxyModel.RasterLayer)
        mRaster.setExcludedProviders(['wms'])
        mRaster.setAllowEmptyLayer(True)
        self.mThresholdingTable.setCellWidget(row, 0, mRaster)

        mBand = QgsRasterBandComboBox()
        mBand.setLayer(mRaster.currentLayer())
        mRaster.layerChanged.connect(mBand.setLayer)
        self.mThresholdingTable.setCellWidget(row, 1, mBand)

        mOperator = QComboBox()
        mOperator.addItems(self.operators)
        self.mThresholdingTable.setCellWidget(row, 2, mOperator)

        mValue = QLineEdit()
        self.mThresholdingTable.setCellWidget(row, 3, mValue)
        mValue.setText('350')

    def onThresholdingRemoveClicked(self):
        row = self.mThresholdingTable.currentRow()
        if row == -1:
            return
        self.mThresholdingTable.removeRow(row)

    def onThresholdingRemoveAllClicked(self):
        for i in reversed(range(self.mThresholdingTable.rowCount())):
            self.mThresholdingTable.removeRow(i)

        # if bandNo is not None:
        #    mMultiBand.mBand.setCurrentIndex(bandNo)

        # self.onLayerChanged()

    def onApplyClicked(self):
        layer = self.mRaster.currentLayer()
        if layer is None:
            return

        for row in range(self.mThresholdingTable.rowCount()):
            mRaster: QgsMapLayerComboBox = self.mThresholdingTable.cellWidget(row, 0)
            mBand: QgsRasterBandComboBox = self.mThresholdingTable.cellWidget(row, 1)
            mOperator: QComboBox = self.mThresholdingTable.cellWidget(row, 2)
            mValue: QLineEdit = self.mThresholdingTable.cellWidget(row, 3)
            print(mRaster.currentLayer(), mBand.currentBand(), mOperator.currentText(), mValue.text())
