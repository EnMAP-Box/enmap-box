import codecs
import os

from enmapbox.gui.dataviews.docks import RX_HTML_FILE, Dock
from enmapbox.gui.dataviews.textdock import TextDockWidget
from enmapbox.gui.utils import enmapboxUiPath
from enmapbox.qgispluginsupport.qps.utils import loadUi
from qgis.PyQt.QtCore import QMimeData, QByteArray, Qt
from qgis.PyQt.QtGui import QTextCursor
from qgis.PyQt.QtWidgets import QTextEdit, QWidget, QFileDialog


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
        formats = [str(f) for f in mimeData.formats()]
        self.mCurrentMimeData = mimeData
        self.clear()

        def append(txt):
            self.moveCursor(QTextCursor.MoveOperation.End)
            self.insertPlainText(txt + '\n')
            self.moveCursor(QTextCursor.MoveOperation.End)

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
        event.setDropAction(Qt.DropAction.CopyAction)  # copy but do not remove
        event.accept()

    def dropEvent(self, event):
        self.insertFromMimeData(event.mimeData())
        event.setDropAction(Qt.DropAction.CopyAction)
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

            if len(path) > 0:
                self.mFile = path

        if self.mFile is not None and len(self.mFile) > 0:
            ext = os.path.splitext(self.mFile)[-1].lower()

            with codecs.open(self.mFile, 'w', 'utf-8') as file:
                if RX_HTML_FILE.search(ext):
                    file.write(self.textEdit.toHtml())
                else:
                    file.write(self.textEdit.toPlainText())


class MimeDataDock(Dock):
    """
    A dock to show dropped mime data
    """

    def __init__(self, *args, **kwds):
        super(MimeDataDock, self).__init__(*args, **kwds)

        self.mimeDataWidget = MimeDataDockWidget(self)
        self.addWidget(self.mimeDataWidget, 0, 0)
