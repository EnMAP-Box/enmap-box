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

from math import ceil
from typing import Optional

from pyqtgraph.dockarea.Dock import Dock as pgDock
from pyqtgraph.dockarea.Dock import DockLabel as pgDockLabel
from qgis.PyQt import QtCore
from qgis.PyQt.QtCore import pyqtSignal, Qt, QPoint
from qgis.PyQt.QtGui import QResizeEvent, \
    QContextMenuEvent
from qgis.PyQt.QtWidgets import QToolButton, QMenu, QMainWindow, QApplication, \
    QStyle, QProgressBar


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
        self._float_area_0 = None
        self.progressBar = self.label.progressBar
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
            from .dockarea import DockArea
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

            self._float_area_0 = None
        self.label.updateStyle()
        self.label.btnFloat.setToolTip('Float window')

    def float(self):
        if self._float_area_0 is None:
            self._float_area_0 = getattr(self, 'orig_area')
        super().float()
        self.label.updateStyle()
        self.label.btnFloat.setToolTip('Move back to main window')

    def toggleFloat(self):
        if self._float_area_0:
            self.unfloat()
        else:
            self.float()


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
        # self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TabCloseButton))
        # self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        # self.closeButton.setIcon(QIcon(r':/qt-project.org/styles/commonstyle/images/closedock-64.png'))
        # self.closeButton.setIcon() SP_TabCloseButton

        self.btnFloat = QToolButton(self)
        self.btnFloat.setToolTip('Float window')
        self.btnFloat.clicked.connect(dock.toggleFloat)
        self.btnFloat.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarNormalButton))
        # self.btnFloat.setIcon(QIcon(':/qt-project.org/styles/commonstyle/images/normalizedockup-32.png'))
        self.btnFloat.setVisible(allow_floating)

        # self.btnUnFloat = QToolButton(self)
        # self.btnUnFloat.setText('U')
        # self.btnUnFloat.setToolTip('Unfloat window')
        # self.btnUnFloat.clicked.connect(dock.unfloat)
        # self.btnUnFloat.setVisible(not allow_floating)

        self.mButtons.extend([self.closeButton, self.btnFloat,
                              # self.btnUnFloat
                              ])

        # add progress bar
        self.progressBar = QProgressBar(self)
        # self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(50)
        self.progressBar.setTextVisible(False)
        self.progressBar.hide()
        self.update()

    def updateStyle(self):
        r = '3px'
        if self.dim:
            # tabbed, in background
            fg = '#aaa'
            # bg = '#44a'
            bg = '#666'
            # border = '#339'
            border = '#333'

        else:
            fg = '#fff'
            bg = '#66c'
            border = '#55B'

        # remove bor
        border = bg
        if self.orientation == 'vertical':
            self.vStyle = """DockLabel {
                background-color : %s;
                color : %s;
                border-top-right-radius: 0px;
                border-top-left-radius: %s;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: %s;
                border-width: 0px;
                border-right: 2px solid %s;
                padding-top: 3px;
                padding-bottom: 3px;
                font-size: %s;
            }""" % (bg, fg, r, r, border, self.fontSize)
            self.setStyleSheet(self.vStyle)
        else:
            self.hStyle = """DockLabel {
                background-color : %s;
                color : %s;
                border-top-right-radius: %s;
                border-top-left-radius: %s;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
                border-width: 0px;
                border-bottom: 2px solid %s;
                padding-left: 3px;
                padding-right: 3px;
                font-size: %s;
            }""" % (bg, fg, r, r, border, self.fontSize)
            self.setStyleSheet(self.hStyle)

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
