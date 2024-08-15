from collections import OrderedDict
from typing import List

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QColor, QPixmap, QIcon, QBrush, QFont
from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox

from enmapbox.typeguard import typechecked
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer
from qgis.gui import QgsDoubleSpinBox, QgsDockWidget


@typechecked
class LandCoverChangeStatisticsDataFilteringDockWidget(QgsDockWidget):
    mTableClasses: QTableWidget
    mFilterBySize: QCheckBox
    mMinClassSize: QgsDoubleSpinBox
    mMaxClassSize: QgsDoubleSpinBox

    sigStateChanged = pyqtSignal()

    def __init__(self, *args, **kwds):
        QgsDockWidget.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mTableClasses.itemClicked.connect(self.onStateChanged)
        self.mFilterBySize.stateChanged.connect(self.onStateChanged)
        self.mMinClassSize.valueChanged.connect(self.onStateChanged)
        self.mMaxClassSize.valueChanged.connect(self.onStateChanged)

    def onClassToggled(self):
        w0: QCheckBox = self.sender()
        for column in range(1, self.mTableClasses.columnCount()):
            for row in range(self.mTableClasses.rowCount()):
                w: QTableWidgetItem = self.mTableClasses.item(row, column)
                if w.text() == w0.text():
                    w.setCheckState(w0.checkState())
        self.onStateChanged()

    def onStateChanged(self):
        self.sigStateChanged.emit()

    def setRelativeClassSizes(self, values: List[List[float]]):
        assert len(values) == self.mTableClasses.columnCount() - 1
        self.relativeClassSizes = values

        # highlight unavailable classes

        highlightedFont = QFont()
        highlightedFont.setItalic(True)
        for column in range(1, self.mTableClasses.columnCount()):
            for row in range(self.mTableClasses.rowCount()):
                w: QTableWidgetItem = self.mTableClasses.item(row, column)
                font = w.font()
                if self.relativeClassSizes[column - 1][row] == 0:
                    color = QColor(200, 200, 200)
                    font.setItalic(True)
                else:
                    color = QColor(0, 0, 0)
                    font.setItalic(False)
                w.setFont(font)
                w.setForeground(QBrush(color))

    def initGui(self, layers: List[QgsRasterLayer]):
        assert len(layers) >= 2

        uniqueCategories = OrderedDict()
        categoriess = list()
        for layer in layers:
            categories = Utils().categoriesFromRenderer(layer.renderer(), layer)
            for c in categories:
                key = c.name
                if key not in uniqueCategories:
                    uniqueCategories[key] = c
            categoriess.append(categories)

        self.mTableClasses.setColumnCount(len(layers) + 1)
        self.mTableClasses.setRowCount(len(uniqueCategories))
        self.mTableClasses.setHorizontalHeaderLabels(['All'] + [l.name() for l in layers])
        for row, c in enumerate(uniqueCategories.values()):
            color = QColor(c.color)
            pixmap = QPixmap(16, 16)
            pixmap.fill(color)
            icon = QIcon(pixmap)
            w = QCheckBox(c.name)
            w.setCheckState(Qt.Checked)
            w.setIcon(icon)
            w.color = color
            w.stateChanged.connect(self.onClassToggled)
            self.mTableClasses.setCellWidget(row, 0, w)
        for column, categories in enumerate(categoriess, 1):
            for row, c in enumerate(categories):
                color = QColor(c.color)
                pixmap = QPixmap(16, 16)
                pixmap.fill(color)
                icon = QIcon(pixmap)
                w = QTableWidgetItem(c.name)
                w.setCheckState(Qt.Checked)
                w.setIcon(icon)
                w.color = color
                self.mTableClasses.setItem(row, column, w)
        self.mTableClasses.resizeColumnsToContents()

    def classFilter(self) -> List[List[str]]:

        if self.mFilterBySize.isChecked():
            vmin = self.mMinClassSize.value() / 100
            vmax = self.mMaxClassSize.value() / 100
        else:
            vmin = 0
            vmax = 1

        names = list()
        for column in range(1, self.mTableClasses.columnCount()):
            inames = list()
            for row in range(self.mTableClasses.rowCount()):
                size = self.relativeClassSizes[column - 1][row]
                w: QTableWidgetItem = self.mTableClasses.item(row, column)
                if w.checkState() != Qt.Checked:  # filtered by local checkbox
                    continue
                if size < vmin or size > vmax:  # filtered by size
                    continue
                inames.append(w.text())
            names.append(inames)
        return names
