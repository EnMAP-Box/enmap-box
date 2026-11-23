from pyqtgraph.dockarea import DockArea as pgDockArea
from pyqtgraph.dockarea.DockArea import TempAreaWindow
from qgis.PyQt.QtCore import pyqtSignal, QObject, QSize
from qgis.PyQt.QtGui import QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent, QIcon

from enmapbox.gui.dataviews.docks import Dock


class DockArea(pgDockArea):
    sigDragEnterEvent = pyqtSignal(QDragEnterEvent)
    sigDragMoveEvent = pyqtSignal(QDragMoveEvent)
    sigDragLeaveEvent = pyqtSignal(QDragLeaveEvent)
    sigDropEvent = pyqtSignal(QDropEvent)

    def __init__(self, *args, **kwds):
        super(DockArea, self).__init__(*args, **kwds)
        self.setAcceptDrops(True)

    def floatDock(self, dock: Dock):
        """Removes *dock* from this DockArea and places it in a new window."""

        # dockLabel: DockLabel = dock.label

        lastArea = dock.area
        super().floatDock(dock)

        if isinstance(lastArea, DockArea):
            lastArea.sigDockRemoved.emit(dock)

        parentWindow = dock.parent()
        while isinstance(parentWindow, QObject) and parentWindow.parent():
            parentWindow = parentWindow.parent()

        if isinstance(parentWindow, TempAreaWindow):
            # dockLabel.btnUnFloat.setVisible(True)
            parentWindow.setWindowTitle('EnMAP-Box')
            parentWindow.setWindowIcon(QIcon(':/enmapbox/gui/ui/icons/enmapbox.svg'))
            parentWindow.resize(QSize(300, 300))

    def apoptose(self):
        try:
            if self.topContainer is not None and self.topContainer.count() == 0:
                self.topContainer = None

            if self.topContainer is None:
                if self.temporary and self.home is not None:
                    self.home.removeTempArea(self)
            else:
                pass
        except Exception:
            self.topContainer = None

    sigDockAdded = pyqtSignal(Dock)
    sigDockRemoved = pyqtSignal(Dock)

    def addTempArea(self):
        if self.home is None:
            area = DockArea(temporary=True, home=self)
            self.tempAreas.append(area)
            win = TempAreaWindow(area)
            area.win = win
            win.show()
        else:
            area = self.home.addTempArea()
        #  print "added temp area", area, area.window()
        return area

    # def addDock(
    #     self,
    #     dock: Union[pgDock, Dock],
    #     position: str = 'bottom',
    #     relativeTo=None,
    #     **kwds
    # ) -> Optional[Dock]:
    #
    #     if hasattr(dock, 'orig_area'):
    #         dock.label.btnUnFloat.setVisible(dock.orig_area != self)
    #
    #     v = None
    #     try:
    #         visibility = dock.isVisible()
    #         v = super(DockArea, self).addDock(dock=dock, position=position, relativeTo=relativeTo, **kwds)
    #         dock.setVisible(visibility)
    #         self.sigDockAdded.emit(dock)
    #     except Exception as ex:
    #         print(f'Failed to add dock:\n{ex}', file=sys.stderr)
    #     return v

    # forward to EnMAPBox
    def dragEnterEvent(self, event):
        super(DockArea, self).dragEnterEvent(event)
        self.sigDragEnterEvent.emit(event)

    # forward to EnMAPBox
    def dragMoveEvent(self, event):
        super(DockArea, self).dragMoveEvent(event)
        self.sigDragMoveEvent.emit(event)

    # forward to EnMAPBox
    def dragLeaveEvent(self, event):
        super(DockArea, self).dragLeaveEvent(event)
        self.sigDragLeaveEvent.emit(event)

    # forward to EnMAPBox
    def dropEvent(self, event):
        super(DockArea, self).dropEvent(event)
        self.sigDropEvent.emit(event)
