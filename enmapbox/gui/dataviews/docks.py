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

import codecs
import os
import re
import typing
import uuid
import warnings
from math import ceil
from typing import List

from enmapbox.gui import SpectralLibraryWidget
from enmapbox.gui.mapcanvas import MapCanvas, CanvasLink
from enmapbox.gui.utils import enmapboxUiPath
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.dockarea import DockArea as pgDockArea
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.dockarea.Dock import Dock as pgDock
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.dockarea.Dock import DockLabel as pgDockLabel
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph.dockarea.DockArea import TempAreaWindow
from enmapbox.qgispluginsupport.qps.utils import loadUi
from enmapboxprocessing.utils import Utils
from qgis.PyQt import QtCore
from qgis.PyQt.QtCore import pyqtSignal, QSettings, Qt, QMimeData, QPoint, QUrl, QObject, QSize, QByteArray
from qgis.PyQt.QtGui import QIcon, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent, QResizeEvent, \
    QContextMenuEvent, QTextCursor
from qgis.PyQt.QtWidgets import QToolButton, QMenu, QMainWindow, QFileDialog, QWidget, QMessageBox, QWidgetItem, \
    QApplication, QStyle, QProgressBar, QTextEdit
from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayer
from qgis.core import QgsLayerTree
from qgis.core import QgsLayerTreeLayer
from qgis.core import QgsVectorLayer
from qgis.gui import QgsMapCanvas

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
        # KeepRefs.__init__(self)
        # ssert enmapboxInstance is not None
        # self.enmapbox = enmapboxInstance
        # self.setStyleSheet('background:#FFF')

        # replace PyQtGraph Label by EnmapBox labels (could be done by inheritances as well)
        title = self.title()
        if True:
            # self.topLayout.addWidget(self.label, 0, 1)
            newLabel = self._createLabel(title=title)
            oldLabel = self.label
            widgetItem = self.topLayout.replaceWidget(oldLabel, newLabel)
            oldLabel.setParent(None)
            assert isinstance(widgetItem, QWidgetItem)
            self.label = newLabel
            if closable:
                self.label.sigCloseClicked.connect(self.close)

        else:
            pass

        self.progressBar = self.label.progressBar
        self.uuid = uuid.uuid4()

        self.raiseOverlay()

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

    def contextMenu(self, menu: QMenu = None):
        warnings.warn('Use populateContextMenu instead', DeprecationWarning)
        self.populateContextMenu(menu)
        return menu

    def populateContextMenu(self, menu: QMenu) -> QMenu:
        """
        implement this to return a QMenu with context menu properties for this dock.
        :return: None or QMenu
        """
        assert isinstance(menu, QMenu)
        if self.isVisible():
            a = menu.addAction('Hide View')
            a.triggered.connect(lambda: self.setVisible(False))
        else:
            a = menu.addAction('Show View')
            a.triggered.connect(lambda: self.setVisible(True))

        a = menu.addAction('Close View')
        a.triggered.connect(lambda: self.close())
        return menu

    sigVisibilityChanged = pyqtSignal(bool)

    def setVisible(self, b: bool):

        i = self.isVisible()
        super(Dock, self).setVisible(b)
        if i != self.isVisible():
            self.sigVisibilityChanged.emit(self.isVisible())

    def setTitle(self, title):
        """
        Override setTitle to emit a signal after title was changed
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

        s = ""

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

        s = ""
    """

    def floatDock(self, dock):
        """Removes *dock* from this DockArea and places it in a new window."""
        assert isinstance(dock, Dock)

        dockLabel: DockLabel = dock.label
        assert isinstance(dockLabel, DockLabel)

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
        except Exception as ex:
            pass

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

    def addDock(self, dock, position='bottom', relativeTo=None, **kwds) -> Dock:
        assert dock is not None

        assert isinstance(dock, Dock)
        if hasattr(dock, 'orig_area'):
            dock.label.btnUnFloat.setVisible(dock.orig_area != self)

        v = None
        try:
            visibility = dock.isVisible()
            v = super(DockArea, self).addDock(dock=dock, position=position, relativeTo=relativeTo, **kwds)
            dock.setVisible(visibility)
            self.sigDockAdded.emit(dock)
        except Exception as ex:
            pass
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
                 dock,
                 title: str = None,
                 allow_floating: bool = True,
                 showClosebutton: bool = True,
                 fontSize: int = 8):
        assert isinstance(dock, Dock)
        if title is None:
            title = dock.title()

        super(DockLabel, self).__init__(title, closable=showClosebutton, fontSize=fontSize)
        self.dock: Dock = dock
        self.mButtons = list()  # think from right to left

        self.setMinimumSize(26, 26)

        self.closeButton: QToolButton
        self.closeButton.setToolTip('Close window')
        self.closeButton.setIcon(QApplication.style().standardIcon(QStyle.SP_TitleBarCloseButton))

        self.btnFloat = QToolButton(self)
        self.btnFloat.setToolTip('Float window')
        self.btnFloat.clicked.connect(dock.float)
        self.btnFloat.setIcon(QApplication.style().standardIcon(QStyle.SP_TitleBarNormalButton))
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

    def contextMenuEvent(self, event):
        assert isinstance(event, QContextMenuEvent)
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
            self.progressBar.setOrientation(Qt.Vertical)
            self.progressBar.setFixedHeight(min(ceil(long_size * relSize), maxSize))
            self.progressBar.setFixedWidth(small_size - 2 * border)
            self.progressBar.move(QPoint(border, long_size - self.progressBar.height() - border))
        else:
            small_size = ev.size().height()
            long_size = ev.size().width()
            self.progressBar.setOrientation(Qt.Horizontal)
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


class MimeDataTextEdit(QTextEdit):

    def __init__(self, *args, **kwargs):
        super(MimeDataTextEdit, self).__init__(*args, **kwargs)
        # self.setLineWrapMode(QTextEdit.FixedColumnWidth)
        self.setOverwriteMode(False)
        self.mCurrentMimeData: QMimeData = QMimeData()

    def canInsertFromMimeData(self, QMimeData) -> bool:
        return True

    def currentMimeData(self) -> QMimeData:
        return self.mCurrentMimeData

    def insertFromMimeData(self, mimeData: QMimeData):
        """
        Shows the QMimeData information
        :param mimeData: QMimeData
        """
        assert isinstance(mimeData, QMimeData)
        formats = [str(f) for f in mimeData.formats()]
        self.mCurrentMimeData = mimeData
        self.clear()

        def append(txt):
            self.moveCursor(QTextCursor.End)
            self.insertPlainText(txt + '\n')
            self.moveCursor(QTextCursor.End)

        for format in formats:
            append('####{}####'.format(format))
            if format == 'text/uri-list':
                self.insertPlainText(str(mimeData.data('text/uri-list')))
            if format == 'text/html':
                self.insertHtml(mimeData.html())
            elif format == 'text/plain':
                self.insertPlainText(mimeData.text())
            else:
                append('### (raw data as string) ###')
                data = mimeData.data(format)
                if isinstance(data, QByteArray):
                    self.insertPlainText(str(mimeData.data(format)))
            append('\n')

    def dragEnterEvent(self, event):
        event.setDropAction(Qt.CopyAction)  # copy but do not remove
        event.accept()

    def dropEvent(self, event):
        self.insertFromMimeData(event.mimeData())
        event.setDropAction(Qt.CopyAction)
        event.accept()


class MimeDataDockWidget(QWidget):

    def __init__(self, parent=None):
        super(MimeDataDockWidget, self).__init__(parent=parent)
        loadUi(enmapboxUiPath('mimedatadockwidget.ui'), self)

    def loadFile(self, path):
        if os.path.isfile(path):
            data = None
            with codecs.open(path, 'r', 'utf-8') as file:
                data = ''.join(file.readlines())

            ext = os.path.splitext(path)[-1].lower()
            if data is not None:
                if RX_HTML_FILE.search(ext):
                    self.textEdit.setHtml(data)
                else:
                    self.textEdit.setText(data)

                self.mFile = path

        else:
            self.mFile = None
        self.sigSourceChanged.emit(str(path))

    def save(self, saveAs=False):
        if self.mFile is None or saveAs:
            path, filter = QFileDialog.getSaveFileName(self, 'Save file...',
                                                       directory=self.mFile,
                                                       filter=TextDockWidget.FILTERS)
            s = ""
            if len(path) > 0:
                self.mFile = path

        if self.mFile is not None and len(self.mFile) > 0:
            ext = os.path.splitext(self.mFile)[-1].lower()

            with codecs.open(self.mFile, 'w', 'utf-8') as file:
                if RX_HTML_FILE.search(ext):
                    file.write(self.textEdit.toHtml())
                else:
                    file.write(self.textEdit.toPlainText())


class TextDockWidget(QWidget):
    """
    A widget to display text files
    """
    FILTERS = ';;'.join(["Text files (*.txt *.csv *.hdr)",
                         "HTML (*.html)",
                         "Any file (*.*)",
                         ])

    sigSourceChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        Constructor
        :param parent:
        """
        super(TextDockWidget, self).__init__(parent=parent)
        loadUi(enmapboxUiPath('textdockwidget.ui'), self)

        self.setAcceptDrops(True)
        self.mFile = None
        self.mTitle = self.windowTitle()
        self.mTextEdit.setAcceptDrops(True)
        self.mTextEdit.dragEnterEven = self.dragEnterEvent
        self.mTextEdit.dropEvent = self.dropEvent
        self.nMaxBytes = 80 * 2 * 12000
        self.btnLoadFile.setDefaultAction(self.actionLoadFile)
        self.btnSaveFile.setDefaultAction(self.actionSaveFile)
        self.btnSaveFileAs.setDefaultAction(self.actionSaveFileAs)
        self.actionLoadFile.triggered.connect(self.onOpenFile)
        self.actionSaveFile.triggered.connect(lambda: self.save(saveAs=False))
        self.actionSaveFileAs.triggered.connect(lambda: self.save(saveAs=True))
        self.actionSaveFile.setEnabled(False)
        self.updateTitle()

    def onOpenFile(self):

        path, result = QFileDialog.getOpenFileName(self, 'Open File', directory=self.mFile,
                                                   filter=TextDockWidget.FILTERS)
        if isinstance(path, str) and len(path) > 0:
            self.loadFile(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        :param event: QDragEnterEvent
        """
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)

            event.accept()

    def dropEvent(self, event: QDropEvent):
        """
        :param event: QDropEvent
        """
        mimeData: QMimeData = event.mimeData()
        if mimeData.hasUrls():
            for url in mimeData.urls():
                if isinstance(url, QUrl) and url.isLocalFile():
                    self.loadFile(url.toLocalFile())
                    event.setDropAction(Qt.CopyAction)
                    event.accept()
                    return

    def file(self) -> str:
        """
        Returns the path of a file added with `loadFile`
        :return: str
        """
        if self.mFile is None:
            return ''
        else:
            return self.mFile

    def loadFile(self, path, *args):
        """
        Loads a text file from `path`
        :param path: str
        """
        if os.path.isfile(path):
            data = None

            statinfo = os.stat(path)
            if statinfo.st_size > self.nMaxBytes:
                info = 'Files {} is > {} bytes'.format(path, self.nMaxBytes)
                info += '\nDo you really want to load it into this text editor?'
                result = QMessageBox.warning(self, 'Warning', info, QMessageBox.Yes, QMessageBox.Cancel)
                if result != QMessageBox.Yes:
                    return
            try:
                with open(path, 'r', 'utf-8') as file:
                    data = ''.join(file.readlines())
            except Exception as ex:
                try:
                    with open(path, 'r') as file:
                        data = ''.join(file.readlines())
                except Exception as ex:
                    pass

            ext = os.path.splitext(path)[-1].lower()
            if data is not None:
                if ext in ['.html']:
                    self.mTextEdit.setHtml(data)
                else:
                    self.mTextEdit.setText(data)

                self.mFile = path

        else:
            self.mFile = None
        self.updateTitle()
        self.actionSaveFile.setEnabled(os.path.isfile(self.file()))
        self.sigSourceChanged.emit(str(path))

    def updateTitle(self):
        """
        Updates the widget title
        """
        # title = '{}'.format(self.mTitle)
        title = ''
        if isinstance(self.mFile, str):
            # title += ' | {}'.format(os.path.basename(self.mFile))
            title = os.path.basename(self.mFile)
        self.setWindowTitle(title)

    def setText(self, *args, **kwds):
        """
        Sets text. See
        :param args:
        :param kwds:
        :return:
        """
        self.mTextEdit.setPlainText(*args, **kwds)

    def text(self) -> str:
        """
        Returns the plain text
        :return: str
        """
        return self.mTextEdit.toPlainText()

    def setHtml(self, *args, **kwds):
        """
        Sets thext as HTML
        :param args:
        :param kwds:
        """
        self.mTextEdit.setHtml(*args, **kwds)

    def save(self, saveAs: bool = False):
        """
        Saves the Text
        :param saveAs: bool
        """
        if self.mFile is None or saveAs:
            path, filter = QFileDialog.getSaveFileName(self, 'Save file...',
                                                       directory=self.mFile,
                                                       filter=TextDockWidget.FILTERS)
            s = ""
            if len(path) > 0:
                self.mFile = path

        if self.mFile is not None and len(self.mFile) > 0:
            ext = os.path.splitext(self.mFile)[-1].lower()

            with codecs.open(self.mFile, 'w', 'utf-8') as file:
                file.write(self.mTextEdit.toPlainText())


class TextDock(Dock):
    """
    A dock to visualize text data
    """

    def __init__(self, *args, **kwds):
        html = kwds.pop('html', None)
        plainTxt = kwds.pop('plainTxt', None)

        super(TextDock, self).__init__(*args, **kwds)

        self.mTextDockWidget = TextDockWidget(self)
        self.mTextDockWidget.windowTitleChanged.connect(self.setTitle)
        if html:
            self.mTextDockWidget.mTextEdit.insertHtml(html)
        elif plainTxt:
            self.mTextDockWidget.mTextEdit.insertPlainText(plainTxt)
        self.layout.addWidget(self.mTextDockWidget)

    def textDockWidget(self) -> TextDockWidget:
        """
        Returns the widget that displays the text
        :return: TextDockWidget
        """
        return self.mTextDockWidget


class WebViewDock(Dock):
    def __init__(self, *args, **kwargs):
        uri = kwargs.pop('uri', None)
        url = kwargs.pop('url', None)
        super(WebViewDock, self).__init__(*args, **kwargs)
        # self.setLineWrapMode(QTextEdit.FixedColumnWidth)

        from qgis.PyQt.QtWebKitWidgets import QWebView
        self.webView = QWebView(self)
        self.layout.addWidget(self.webView)

        if uri is not None:
            self.load(uri)
        elif url is not None:
            self.load(url)

    def load(self, uri):
        if os.path.isfile(uri):
            url = QUrl.fromLocalFile(uri)
        else:
            url = QUrl(uri)
        self.webView.load(url)
        settings = self.webView.page().settings()
        from qgis.PyQt.QtWebKit import QWebSettings
        settings.setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebSettings.AutoLoadImages, True)


class AttributeTableDock(Dock):
    """
    A dock to show a VectorLayer attribute table
    """

    def __init__(self, layer: QgsVectorLayer, *args, **kwds):
        super(AttributeTableDock, self).__init__(*args, **kwds)
        from enmapbox.qgispluginsupport.qps.layerproperties import AttributeTableWidget
        self.attributeTableWidget = AttributeTableWidget(layer)
        self.addWidget(self.attributeTableWidget, 0, 0)
        self.updateTitle(self.attributeTableWidget.windowTitle())
        self.attributeTableWidget.windowTitleChanged.connect(self.updateTitle)

    def updateTitle(self, title: str):
        # we need to get a short name, not the entire title
        self.setTitle(title.split('::')[0])

    def vectorLayer(self) -> QgsVectorLayer:
        return self.attributeTableWidget.mLayer


class MimeDataDock(Dock):
    """
    A dock to show dropped mime data
    """

    def __init__(self, *args, **kwds):
        super(MimeDataDock, self).__init__(*args, **kwds)

        self.mimeDataWidget = MimeDataDockWidget(self)
        self.addWidget(self.mimeDataWidget, 0, 0)


class SpectralLibraryDock(Dock):
    """
    A Dock to show SpectralProfiles
    """
    sigLoadFromMapRequest = pyqtSignal()

    def __init__(self, *args, speclib: QgsVectorLayer = None, **kwds):
        super(SpectralLibraryDock, self).__init__(*args, **kwds)

        self.mSpeclibWidget: SpectralLibraryWidget = SpectralLibraryWidget(parent=self, speclib=speclib)
        self.mSpeclibWidget.spectralLibraryPlotWidget().optionShowVisualizationSettings.setChecked(False)
        self.mSpeclibWidget.sigLoadFromMapRequest.connect(self.sigLoadFromMapRequest)
        self.layout.addWidget(self.mSpeclibWidget)

        speclib: QgsVectorLayer = self.mSpeclibWidget.speclib()

        name = kwds.get('name')
        if isinstance(name, str):
            speclib.setName(name)

        self.setTitle(speclib.name())
        speclib.nameChanged.connect(lambda slib=speclib: self.setTitle(slib.name()))
        self.sigTitleChanged.connect(speclib.setName)

    def speclibWidget(self) -> SpectralLibraryWidget:
        """
        Returns the SpectralLibraryWidget
        :return: SpectralLibraryWidget
        """
        return self.mSpeclibWidget

    def speclib(self) -> QgsVectorLayer:
        """Returns the underlying spectral library"""
        return self.mSpeclibWidget.speclib()

    def populateContextMenu(self, menu: QMenu):
        """
        Returns the MapDock context menu
        :return: QMenu
        """
        super(SpectralLibraryDock, self).populateContextMenu(menu)

        # here we might add Spectral Library Widget specific action
        # speclib / vector layer specific ones are accessible via the lower node

        slw = self.speclibWidget()
        if isinstance(slw, SpectralLibraryWidget):
            menu.addSeparator()
            for action in slw.tbSpeclibAction.actions():
                menu.addAction(action)


class MapDockLabel(DockLabel):

    def __init__(self, *args, **kwds):
        super(MapDockLabel, self).__init__(*args, **kwds)

        self.addMapLink = QToolButton(self)
        self.addMapLink.setToolTip('Link with other map(s)')
        self.addMapLink.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_basic.svg'))
        self.mButtons.append(self.addMapLink)

        self.removeMapLink = QToolButton(self)
        self.removeMapLink.setToolTip('Remove links to this map')
        self.removeMapLink.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_open.svg'))
        self.mButtons.append(self.removeMapLink)


class MapDock(Dock):
    """
    A dock to visualize geodata that can be mapped
    """

    ISSUE_1344_REFERENCES: List[MapCanvas] = []

    sigLayersAdded = pyqtSignal(list)
    sigLayersRemoved = pyqtSignal(list)
    sigCrsChanged = pyqtSignal(QgsCoordinateReferenceSystem)
    sigRenderStateChanged = pyqtSignal()  # used by the progress bar

    def __init__(self, *args, **kwds):
        initSrc = kwds.pop('initSrc', None)
        super(MapDock, self).__init__(*args, **kwds)
        self.mBaseName = self.title()

        from enmapbox.gui.mapcanvas import MapCanvas
        self.mCanvas: MapCanvas = MapCanvas(self)
        self.mCanvas.setWindowTitle(self.title())
        self.mCanvas.sigNameChanged.connect(self.setTitle)
        self.mCanvas.sigCrsChanged.connect(self.sigCrsChanged.emit)

        self.sigTitleChanged.connect(self.mCanvas.setWindowTitle)

        settings = QSettings()
        assert isinstance(self.mCanvas, QgsMapCanvas)
        self.mCanvas.setCanvasColor(Qt.black)
        self.mCanvas.enableAntiAliasing(settings.value('/qgis/enable_anti_aliasing', False, type=bool))
        self.layout.addWidget(self.mCanvas)

        # connect progress bar to render state
        self.mCanvas.renderStarting.connect(self.showProgressBar)
        self.mCanvas.renderComplete.connect(self.hideProgressBar)
        self.mCanvas.renderErrorOccurred.connect(self.hideProgressBar)

    def close(self):
        if isinstance(self.mCanvas, QgsMapCanvas):
            self.layout.takeAt(self.layout.indexOf(self.mCanvas))
            self.mCanvas.setVisible(False)
            self.mCanvas.setParent(None)
            if self.mCanvas not in self.ISSUE_1344_REFERENCES:
                self.ISSUE_1344_REFERENCES.append(self.mCanvas)
            if self.mCanvas in MapCanvas._instances:
                MapCanvas._instances.remove(self.mCanvas)

        super().close()

    def layerTree(self) -> QgsLayerTree:
        """
        Returns the layer tree that controls the MapCanvas layers.
        Can be none in case the MapCanvas is not linked to a layer tree
        :return: QgsLayerTree
        """
        return self.mapCanvas().layerTree()

    def showProgressBar(self):
        self.progressBar.setRange(0, 0)
        self.progressBar.show()

    def hideProgressBar(self):
        self.progressBar.hide()

    def treeNode(self) -> QgsLayerTree:
        return self.layerTree()

    def removeLayer(self, layer: QgsMapLayer):
        self.treeNode().removeLayer(layer)

    def mapCanvas(self) -> MapCanvas:
        return self.mCanvas

    def populateContextMenu(self, menu: QMenu):
        """
        Returns the MapDock context menu
        :return: QMenu
        """
        super(MapDock, self).populateContextMenu(menu)

        self.mCanvas.populateContextMenu(menu, None)
        return menu

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            s = ""
        else:
            super(MapDock, self).mousePressEvent(event)

    def linkWithMapDock(self, mapDock, linkType) -> CanvasLink:
        assert isinstance(mapDock, MapDock)
        return self.linkWithCanvas(mapDock.mCanvas, linkType)

    def linkWithCanvas(self, canvas, linkType) -> CanvasLink:
        assert isinstance(canvas, QgsMapCanvas)
        return self.mapCanvas().createCanvasLink(canvas, linkType)

    def addLayers(self, layers: typing.List[QgsMapLayer]):
        tree: QgsLayerTree = self.layerTree()
        for lyr in layers:
            tree.addLayer(lyr)

    def insertLayer(self, idx, layerSource):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        from enmapbox.gui.dataviews.dockmanager import MapDockTreeNode

        enmapBox = EnMAPBox.instance()
        if enmapBox is not None:
            mapDockTreeNode: MapDockTreeNode
            for mapDockTreeNode in enmapBox.dockManagerTreeModel().mapDockTreeNodes():
                if mapDockTreeNode.dock is self:
                    mapDockTreeNode.insertLayer(idx=idx, layerSource=layerSource)

    def addOrUpdateLayer(self, layer: QgsMapLayer):
        """Add a new layer or update existing layer with matching name."""

        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox.instance()

        # look for existing layer and update ...
        layerNode: QgsLayerTreeLayer
        for index, layerNode in enumerate(self.treeNode().findLayers()):
            if layer.name() == layerNode.layer().name():
                if False and layer.dataProvider().name() == layerNode.layer().dataProvider().name():
                    Utils.setLayerDataSource(
                        layerNode.layer(), layer.dataProvider().name(), layer.source(), layer.extent()
                    )
                    layerNode.layer().setRenderer(layer.renderer().clone())
                    self.mapCanvas().refresh()
                    enmapBox.layerTreeView().refreshLayerSymbology(layerNode.layer().id())
                    return
                else:
                    # different providers can cause problems, so we better remove the existing and insert the new layer

                    # self.insertLayer(index, layer)  # currently broken, see issue #881

                    self.addLayers([layer])
                    self.removeLayer(layerNode.layer())

                    return

        # ... or add the layer
        self.addLayers([layer])


class DockTypes(object):
    """
    Enumeration that defines the standard dock types.
    """
    MapDock = 'MAP'
    TextDock = 'TEXT'
    MimeDataDock = 'MIME'
    WebViewDock = 'WEBVIEW'
    SpectralLibraryDock = 'SPECLIB'
    AttributeTableDock = 'ATTRIBUTES'


LUT_DOCKTYPES = {DockTypes.MapDock: MapDock,
                 DockTypes.TextDock: TextDock,
                 DockTypes.MimeDataDock: MimeDataDock,
                 DockTypes.WebViewDock: WebViewDock,
                 DockTypes.SpectralLibraryDock: SpectralLibraryDock,
                 DockTypes.AttributeTableDock: AttributeTableDock
                 }

for cls in set(LUT_DOCKTYPES.values()):
    LUT_DOCKTYPES[cls] = cls
