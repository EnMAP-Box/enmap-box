from typing import List, Optional

from qgis.PyQt.uic import loadUi

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWidget, QLineEdit, QToolButton, QListWidget, QListWidgetItem, QDialog
from qgis.core import QgsMapLayer, QgsProject, QgsCoordinateReferenceSystem, QgsRasterLayer, QgsVectorLayer
from typeguard import typechecked


@typechecked
class MultipleMapLayerSelectionWidget(QWidget):
    mInfo: QLineEdit
    mButton: QToolButton

    mLayers: List[QgsMapLayer]

    def __init__(self, parent=None, allowRaster=True, allowVector=True):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.allowRaster = allowRaster
        self.allowVector = allowVector

        self.mLayers = list()

        self.mButton.clicked.connect(self.onButtonClicked)
        QgsProject.instance().layersRemoved.connect(self.onLayersRemoved)

        self.updateInfo()

    def currentLayers(self) -> List[QgsMapLayer]:
        return list(self.mLayers)

    def setCurrentLayers(self, layers: List[QgsMapLayer]):
        self.mLayers = list(layers)

    def updateInfo(self):
        self.mInfo.setText(f'{len(self.mLayers)} layers selected')

    def onButtonClicked(self):
        layers = MultipleMapLayerSelectionDialog.getLayers(
            self, self.currentLayers(), self.allowRaster, self.allowVector
        )
        if layers is not None:
            self.mLayers = layers
            self.updateInfo()

    def onLayersRemoved(self, layerIds: List[str]):
        self.mLayers = list(QgsProject.instance().mapLayers().values())
        self.updateInfo()


@typechecked
class MultipleMapLayerSelectionDialog(QDialog):
    mList: QListWidget
    mSelectAll: QToolButton
    mClearSelection: QToolButton
    mToggleSelection: QToolButton
    mOk: QToolButton
    mCancel: QToolButton

    def __init__(
            self, parent=None, selection: List[QgsMapLayer] = None, allowRaster=True, allowVector=True
    ):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('widget.py', 'dialog.ui'), self)
        self.accepted = False

        # self.mLayers = list()
        layer: QgsMapLayer
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsRasterLayer) and not allowRaster:
                continue
            if isinstance(layer, QgsVectorLayer) and not allowVector:
                continue
            crs: QgsCoordinateReferenceSystem = layer.crs()
            item = QListWidgetItem(f'{layer.name()} [{crs.authid()}]')
            item.layer = layer
            if selection is not None and layer in selection:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.mList.addItem(item)
            # self.mLayers.append(layer)

        self.mOk.clicked.connect(self.onOkClicked)
        self.mCancel.clicked.connect(self.close)
        self.mSelectAll.clicked.connect(self.onSelectAllClicked)
        self.mClearSelection.clicked.connect(self.onClearSelectionClicked)
        self.mToggleSelection.clicked.connect(self.onToggleSelectionClicked)

    def currentLayers(self) -> List[QgsMapLayer]:
        layers = list()
        for row in range(self.mList.count()):
            item = self.mList.item(row)
            if item.checkState() == Qt.Checked:
                layers.append(item.layer)
        return layers

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
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)

    @staticmethod
    def getLayers(
            parent=None, selection: List[QgsMapLayer] = None, allowRaster=True, allowVector=True
    ) -> Optional[List[QgsMapLayer]]:
        w = MultipleMapLayerSelectionDialog(
            parent, selection, allowRaster=allowRaster, allowVector=allowVector
        )
        w.exec()

        if w.accepted:
            return w.currentLayers()
        else:
            return None
