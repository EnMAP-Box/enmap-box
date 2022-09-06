from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QCursor, QColor
from qgis.PyQt.QtWidgets import QAction

from qgis.gui import QgsMapTool, QgsMapMouseEvent, QgsMapCanvas, QgsVertexMarker
from typeguard import typechecked


@typechecked
class MapTool(QgsMapTool):
    sigClicked = pyqtSignal(QgsMapMouseEvent)

    def __init__(self, canvas: QgsMapCanvas, toolBarIcon: QAction):
        QgsMapTool.__init__(self, canvas)

        self.toolBarIcon = toolBarIcon

        # init map canvas items
        self.crosshairItem = QgsVertexMarker(mapCanvas=canvas)
        self.crosshairItem.setColor(QColor(255, 0, 0))
        self.crosshairItem.setIconSize(9999999)
        self.crosshairItem.setIconType(QgsVertexMarker.ICON_CROSS)
        self.crosshairItem.setPenWidth(0)
        self.crosshairItem.setVisible(self.toolBarIcon.isChecked())

    def activate(self):
        QgsMapTool.activate(self)
        self.canvas().setCursor(QCursor(Qt.CrossCursor))

        self.toolBarIcon.setChecked(True)
        self.crosshairItem.setVisible(True)

    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.toolBarIcon.setChecked(False)
        self.crosshairItem.setVisible(False)

    def canvasReleaseEvent(self, event: QgsMapMouseEvent):
        event.accept()

        self.crosshairItem.setCenter(event.originalMapPoint())
        self.sigClicked.emit(event)
