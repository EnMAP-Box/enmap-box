import os
import warnings
from pathlib import Path
from typing import Union

from qgis.PyQt.QtCore import Qt, QMimeData, QUrl
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QDragEnterEvent, QDropEvent
from qgis.PyQt.QtWidgets import QWidget, QFileDialog, QMessageBox

from enmapbox.gui.dataviews.docks import Dock
from enmapbox.gui.utils import enmapboxUiPath
from enmapbox.qgispluginsupport.qps.utils import loadUi


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
        self.mFile: str | None = None
        self.mTitle = self.windowTitle()
        self.mTextEdit.setAcceptDrops(True)
        self.mTextEdit.dragEnterEven = self.dragEnterEvent
        self.mTextEdit.dropEvent = self.dropEvent
        self.nMaxBytes = 80 * 2 * 12000
        self.btnLoadFile.setDefaultAction(self.actionLoadFile)
        self.btnSaveFile.setDefaultAction(self.actionSaveFile)
        self.btnSaveFileAs.setDefaultAction(self.actionSaveFileAs)
        self.actionLoadFile.triggered.connect(self.onOpenFile)
        self.actionSaveFile.triggered.connect(lambda: self.saveFile(saveAs=False))
        self.actionSaveFileAs.triggered.connect(lambda: self.saveFile(saveAs=True))
        self.actionSaveFile.setEnabled(False)
        self.updateTitle()

    def onOpenFile(self):

        path, result = QFileDialog.getOpenFileName(self, 'Open File', directory=self.mFile,
                                                   filter=TextDockWidget.FILTERS)
        if isinstance(path, str) and len(path) > 0:
            self.setFile(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        :param event: QDragEnterEvent
        """
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)

            event.accept()

    def dropEvent(self, event: QDropEvent):
        """
        :param event: QDropEvent
        """
        mimeData: QMimeData = event.mimeData()
        if mimeData.hasUrls():
            for url in mimeData.urls():
                if isinstance(url, QUrl) and url.isLocalFile():
                    self.setFile(url.toLocalFile())
                    event.setDropAction(Qt.DropAction.CopyAction)
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

    def loadFile(self, *args, **kwds):
        warnings.warn('Use setFile', DeprecationWarning, stacklevel=2)
        self.setFile(*args, **kwds)

    def setFile(self, path: Union[str, Path], *args):
        """
        Loads a text file from `path`
        :param path: str
        """
        path = Path(path)
        if path.is_file():
            data = None
            statinfo = os.stat(path)
            if statinfo.st_size > self.nMaxBytes:
                info = 'Files {} is > {} bytes'.format(path, self.nMaxBytes)
                info += '\nDo you really want to load it into this text editor?'
                result = QMessageBox.warning(
                    self, 'Warning', info,
                    QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Cancel
                )
                if result != QMessageBox.StandardButton.Yes:
                    return

            with open(path, 'r') as file:
                data = ''.join(file.readlines())

            ext = os.path.splitext(path)[-1].lower()
            if data is not None:
                if ext in ['.html']:
                    self.mTextEdit.setHtml(data)
                else:
                    self.mTextEdit.setText(data)

                self.mFile = str(path)

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

    def save(self, *args, **kwds):
        warnings.warn('Use setFile', DeprecationWarning, stacklevel=2)
        self.saveFile(*args, **kwds)

    def saveFile(self,
                 path: str | Path | None = None,
                 saveAs: bool = False):
        """
        Saves the Text
        :param path: str | Path with filepath to save the text
        :param saveAs: bool. Set True to open a save-as-file dialog, e.g. to change the file location
        """
        if path is None:
            path = self.mFile

        if path is None or saveAs:
            path, filter = QFileDialog.getSaveFileName(self, 'Save file...',
                                                       directory=self.mFile,
                                                       filter=TextDockWidget.FILTERS)

        if path is not None:
            path = str(path)
            if len(path) > 0:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(self.mTextEdit.toPlainText())
                self.mFile = path

        self.updateTitle()


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
