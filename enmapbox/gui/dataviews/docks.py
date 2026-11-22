# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    docks.py
    ---------------------
    Date                 : August 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import re
import sys
from math import ceil
from typing import Optional, Union

from pyqtgraph.dockarea import DockArea as pgDockArea
from pyqtgraph.dockarea.Dock import Dock as pgDock
from pyqtgraph.dockarea.Dock import DockLabel as pgDockLabel
from pyqtgraph.dockarea.DockArea import TempAreaWindow
from qgis.PyQt import QtCore
from qgis.PyQt.QtCore import pyqtSignal, Qt, QPoint, QObject, QSize
from qgis.PyQt.QtGui import QIcon, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent, QResizeEvent, \
    QContextMenuEvent
from qgis.PyQt.QtWidgets import QToolButton, QMenu, QMainWindow, QApplication, \
    QStyle, QProgressBar

RX_HTML_FILE = re.compile(r'\.(html|html|xhtml)$', re.I)


class DockWindow(QMainWindow):
    def __init__(self, area, **kwargs):
        QMainWindow.__init__(self, **kwargs)
        self.setWindowTitle('EnMAPBox')
        import enmapbox.gui.enmapboxgui
        self.setWindowIcon(enmapbox.icon())
        self.setCentralWidget(area)

    def closeEvent(self, *args, **kwargs):
        self.centralWidget().clear()


class Dock(pgDock):
    @staticmethod
    def readXml(elem):

        return None

    '''
    Handle style sheets etc., basic stuff that differs from pyqtgraph dockarea
    '''
    sigTitleChanged = pyqtSignal(str)

    def __init__(self, name='Data View', closable=True, *args, **kwds):
        super().__init__(name=name, closable=closable, *args, **kwds)

        self.mEnMAPBox = None

        # replace PyQtGraph Label by EnmapBox labels (could be done by inheritances as well)
        title = self.title()
        if True:
            # self.topLayout.addWidget(self.label, 0, 1)
            newLabel = self._createLabel(title=title)
            oldLabel = self.label
            # widgetItem: QWidgetItem = self.topLayout.replaceWidget(oldLabel, newLabel)
            oldLabel.setParent(None)
            self.label = newLabel
            if closable:
                self.label.sigCloseClicked.connect(self.close)

        else:
            pass

        self.progressBar = self.label.progressBar
        # self.uuid = uuid.uuid4()

        # self.raiseOverlay()

        if False:
            self.hStyle = """
            Dock > QWidget {
                border: 1px solid #000;
                border-radius: 1px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-top-width: 0px;
            }
            """
            self.vStyle = """
            Dock > QWidget {
                border: 1px solid #000;
                border-radius: 1px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-left-width: 0px;
            }
            """
            self.nStyle = """
            Dock > QWidget {
                border: 1px solid #000;
                border-radius: 1px;
            }"""
            self.dragStyle = """
            Dock > QWidget {
                border: 4px solid #00F;
                border-radius: 1px;
            }"""

            self.widgetArea.setStyleSheet(self.hStyle)
        self.topLayout.update()

    def populateContextMenu(self, menu: QMenu) -> QMenu:
        """
        implement this to return a QMenu with context menu properties for this dock.
        :return: None or QMenu
        """

        return menu

    sigVisibilityChanged = pyqtSignal(bool)

    def setVisible(self, b: bool):

        i = self.isVisible()
        super(Dock, self).setVisible(b)
        if i != self.isVisible():
            self.sigVisibilityChanged.emit(self.isVisible())

    def setTitle(self, title: str):
        """
        Override setTitle to emit a signal after the title was changed
        :param title:
        :return:
        """

        old = self.title()
        super(Dock, self).setTitle(title)
        if old != title:
            self.sigTitleChanged.emit(title)

    def _createLabel(self, *args, **kwds):
        """
        Override this function to provide a dock-specific label
        :return:
        """
        return DockLabel(self, *args, **kwds)

    def append_hv_style(self, stylestr):
        obj_name = type(self).__name__
        style = ' \n{} {{\n{}\n}} '.format(obj_name, stylestr)
        self.hStyle += style
        self.vStyle += style

    def setEnMAPBox(self, enmapBox):
        self.mEnMAPBox = enmapBox

    def enmapBox(self):
        return self.mEnMAPBox

    def addTempArea(self):
        if self.home is None:
            area = DockArea(temporary=True, home=self)
            self.tempAreas.append(area)
            win = DockWindow(area)
            area.win = win
            win.show()
        else:
            area = self.home.addTempArea()
        return area

    def setOrientation(self, o='auto', force=False):
        """
        Sets the orientation of the title bar for this Dock.
        Must be one of 'auto', 'horizontal', or 'vertical'.
        By default ('auto'), the orientation is determined
        based on the aspect ratio of the Dock.
        """
        # print self.name(), "setOrientation", o, force
        if o == 'auto' and self.autoOrient:
            # if self.container().type() == 'tab':
            if self.container() is None or self.container().type() == 'tab':
                o = 'horizontal'
            elif self.width() > self.height() * 1.5:
                o = 'vertical'
            else:
                o = 'horizontal'
        if force or self.orientation != o:
            self.orientation = o
            self.label.setOrientation(o)
            self.updateStyle()

    def unfloat(self, *args):
        if hasattr(self, 'orig_area'):
            self.setVisible(True)
            self.orig_area.moveDock(self, 'left', None)


class DockArea(pgDockArea):
    sigDragEnterEvent = pyqtSignal(QDragEnterEvent)
    sigDragMoveEvent = pyqtSignal(QDragMoveEvent)
    sigDragLeaveEvent = pyqtSignal(QDragLeaveEvent)
    sigDropEvent = pyqtSignal(QDropEvent)

    def __init__(self, *args, **kwds):
        super(DockArea, self).__init__(*args, **kwds)
        self.setAcceptDrops(True)

    def makeContainer(self, typ):
        c = super(DockArea, self).makeContainer(typ)
        # c.apoptose = lambda x : DockArea.containerApoptose(c, x)
        # c.apoptose = lambda p : DockArea.containerApoptose(c,p)
        # c.apoptose(True)
        return c

    """
    #todo: somehow manipulate this to solve issue #21
    #ask user to really close DockArea if more than one dock is opened
    #"Do you really want to close this window and all contents?"
    @staticmethod
    def containerApoptose(self, propagate):
        ##if there is only one (or zero) item in this container, disappear.
        cont = self._container
        c = self.count()
        if c > 1:
            return
        if self.count() == 1:  ## if there is one item, give it to the parent container (unless this is the top)
            if self is self.area.topContainer:
                return
            self.container().insert(self.widget(0), 'before', self)
        # print "apoptose:", self
        self.close()
        if propagate and cont is not None:
            cont.apoptose()

    def fixDock(self, dock):

        pass
    """

    def floatDock(self, dock: Dock):
        """Removes *dock* from this DockArea and places it in a new window."""

        dockLabel: DockLabel = dock.label

        lastArea = dock.area
        super().floatDock(dock)

        if isinstance(lastArea, DockArea):
            lastArea.sigDockRemoved.emit(dock)

        parentWindow = dock.parent()
        while isinstance(parentWindow, QObject) and parentWindow.parent():
            parentWindow = parentWindow.parent()

        if isinstance(parentWindow, TempAreaWindow):
            dockLabel.btnUnFloat.setVisible(True)
            parentWindow.setWindowTitle('EnMAP-Box')
            parentWindow.setWindowIcon(QIcon(':/enmapbox/gui/ui/icons/enmapbox.svg'))
            # fix for https://bitbucket.org/hu-geomatics/enmap-box/issues/
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

    def addDock(
        self,
        dock: Union[pgDock, Dock],
        position: str = 'bottom',
        relativeTo=None,
        **kwds
    ) -> Optional[Dock]:

        if hasattr(dock, 'orig_area'):
            dock.label.btnUnFloat.setVisible(dock.orig_area != self)

        v = None
        try:
            visibility = dock.isVisible()
            v = super(DockArea, self).addDock(dock=dock, position=position, relativeTo=relativeTo, **kwds)
            dock.setVisible(visibility)
            self.sigDockAdded.emit(dock)
        except Exception as ex:
            print(f'Failed to add dock:\n{ex}', file=sys.stderr)
        return v

    # forward to EnMAPBox
    def dragEnterEvent(self, event):
        self.sigDragEnterEvent.emit(event)

    # forward to EnMAPBox
    def dragMoveEvent(self, event):

        self.sigDragMoveEvent.emit(event)

    # forward to EnMAPBox
    def dragLeaveEvent(self, event):

        self.sigDragLeaveEvent.emit(event)

    # forward to EnMAPBox
    def dropEvent(self, event):
        self.sigDropEvent.emit(event)


class DockLabel(pgDockLabel):
    sigClicked = pyqtSignal(object, object)
    sigCloseClicked = pyqtSignal()
    sigNormalClicked = pyqtSignal()
    sigContextMenuRequest = pyqtSignal(QContextMenuEvent)

    def __init__(self,
                 dock: Dock,
                 title: Optional[str] = None,
                 allow_floating: bool = True,
                 showClosebutton: bool = True,
                 fontSize: int = 8):

        if title is None:
            title = dock.title()

        super(DockLabel, self).__init__(title, closable=showClosebutton, fontSize=fontSize)
        self.dock: Dock = dock
        self.mButtons = list()  # think from right to left

        self.setMinimumSize(26, 26)

        self.closeButton: QToolButton
        self.closeButton.setToolTip('Close window')
        self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))

        self.btnFloat = QToolButton(self)
        self.btnFloat.setToolTip('Float window')
        self.btnFloat.clicked.connect(dock.float)
        self.btnFloat.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarNormalButton))
        self.btnFloat.setVisible(allow_floating)

        self.btnUnFloat = QToolButton(self)
        self.btnUnFloat.setText('U')
        self.btnUnFloat.setToolTip('Unfloat window')
        self.btnUnFloat.clicked.connect(dock.unfloat)
        self.btnUnFloat.setVisible(not allow_floating)

        self.mButtons.extend([self.closeButton, self.btnFloat, self.btnUnFloat])

        # add progress bar
        self.progressBar = QProgressBar(self)
        # self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(50)
        self.progressBar.setTextVisible(False)
        self.progressBar.hide()
        self.update()

    def contextMenuEvent(self, event: QContextMenuEvent):
        self.sigContextMenuRequest.emit(event)

    # def mouseMoveEvent(self, ev):
    #    if not self.startedDrag and hasattr(self, 'pressPos'):
    #        super(DockLabel, self).mouseMoveEvent(ev)
    #    else:
    #        ev.accept()

    def resizeEvent(self, ev: QResizeEvent):
        border = 0
        relSize = 0.2
        maxSize = 50

        if self.orientation == 'vertical':
            small_size = ev.size().width()
            long_size = ev.size().height()
            self.progressBar.setOrientation(Qt.Orientation.Vertical)
            self.progressBar.setFixedHeight(min(ceil(long_size * relSize), maxSize))
            self.progressBar.setFixedWidth(small_size - 2 * border)
            self.progressBar.move(QPoint(border, long_size - self.progressBar.height() - border))
        else:
            small_size = ev.size().height()
            long_size = ev.size().width()
            self.progressBar.setOrientation(Qt.Orientation.Horizontal)
            self.progressBar.setFixedWidth(min(ceil(long_size * relSize), maxSize))
            self.progressBar.setFixedHeight(small_size - 2 * border)
            self.progressBar.move(QPoint(border, border))

        for i, btn in enumerate([b for b in self.mButtons if not b.isHidden()]):
            if self.orientation == 'vertical':
                pos = QtCore.QPoint(0, i * small_size)
            else:
                pos = QtCore.QPoint(ev.size().width() - (i + 1) * small_size, 0)
            btn.setFixedSize(QtCore.QSize(small_size, small_size))
            btn.move(pos)

        super(DockLabel, self).resizeEvent(ev)
