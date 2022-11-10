from typing import List, Optional

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QListWidget, QListWidgetItem, QDialog
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer, QgsMapLayer
from qgis.gui import QgsRasterBandComboBox
from typeguard import typechecked


@typechecked
class MultipleRasterBandSelectionWidget(QWidget):
    mBand: QgsRasterBandComboBox
    mButton: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.uri: Optional[str] = None
        self.bandNumbers: List[int] = list()
        self.mButton.clicked.connect(self.onButtonClicked)
        self.mBand.setShowNotSetOption(True, '0 band(s) selected')
        self.updateInfo()

    def currentBands(self) -> List[int]:
        if self.mBand.currentIndex() == 0:
            return list(self.bandNumbers)
        else:
            return [self.mBand.currentIndex()]

    def currentLayer(self) -> Optional[QgsRasterLayer]:
        layer = self.mBand.layer()
        if layer is not None:
            return layer
        if self.uri is not None:
            return QgsRasterLayer(self.uri)
        return None

    def setLayer(self, layer: Optional[QgsRasterLayer]):
        self.mBand.setLayer(layer)
        if layer is None:
            self.uri = None
        else:
            self.uri = layer.source()

    def setCurrentBands(self, bandNumbers: List[int] = None):
        if bandNumbers is None:
            bandNumbers = list(range(1, self.currentLayer().bandCount() + 1))
        self.bandNumbers = list(bandNumbers)
        self.mBand.setCurrentIndex(0)
        self.updateInfo()

    def setCurrentBand(self, bandNumber: int):
        self.bandNumbers = [bandNumber]
        self.mBand.setBand(bandNumber)
        self.updateInfo()

    def updateInfo(self):
        self.mBand.setItemText(0, f'{len(self.bandNumbers)} band(s) selected')

    def onButtonClicked(self):
        layer = self.currentLayer()
        if layer is None:
            return
        selection = self.currentBands()
        bandNames = [layer.bandName(bandNo) for bandNo in range(1, layer.bandCount() + 1)]
        selection = MultipleRasterBandSelectionDialog.getBands(self, selection, bandNames)
        if selection is not None:
            self.setCurrentBands(selection)
            self.updateInfo()


@typechecked
class MultipleRasterBandSelectionDialog(QDialog):
    mList: QListWidget
    mSelectAll: QToolButton
    mClearSelection: QToolButton
    mToggleSelection: QToolButton
    mOk: QToolButton
    mCancel: QToolButton

    def __init__(self, parent=None, selection: List[int] = None, bandNames: List[str] = None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('widget.py', 'dialog.ui'), self)
        assert selection is not None
        assert bandNames is not None

        self.accepted = False

        layer: QgsMapLayer
        for bandNo, bandName in enumerate(bandNames, 1):
            item = QListWidgetItem(bandName)
            item.bandNo = bandNo
            if bandNo in selection:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.mList.addItem(item)

        self.mOk.clicked.connect(self.onOkClicked)
        self.mCancel.clicked.connect(self.close)
        self.mSelectAll.clicked.connect(self.onSelectAllClicked)
        self.mClearSelection.clicked.connect(self.onClearSelectionClicked)
        self.mToggleSelection.clicked.connect(self.onToggleSelectionClicked)

    def currentBands(self) -> List[int]:
        bandNumbers = list()
        for row in range(self.mList.count()):
            item = self.mList.item(row)
            if item.checkState() == Qt.Checked:
                bandNumbers.append(item.bandNo)
        return bandNumbers

    def onOkClicked(self):
        self.accepted = True
        self.close()

    def onSelectAllClicked(self):
        for row in range(self.mList.count()):
            item = self.mList.item(row)
            item.setCheckState(Qt.Checked)

    def onClearSelectionClicked(self):
        for row in range(self.mList.count()):
            item = self.mList.item(row)
            item.setCheckState(Qt.Unchecked)

    def onToggleSelectionClicked(self):
        for row in range(self.mList.count()):
            item = self.mList.item(row)
            if not item.isSelected():
                continue
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)

    @staticmethod
    def getBands(parent=None, selection: List[int] = None, bandNames: List[str] = None) -> Optional[List[int]]:
        dialog = MultipleRasterBandSelectionDialog(parent, selection, bandNames)
        dialog.exec()

        if dialog.accepted:
            return dialog.currentBands()
        else:
            return None
