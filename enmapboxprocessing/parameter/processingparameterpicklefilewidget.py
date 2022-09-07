from os.path import basename, join, dirname

from qgis.PyQt.uic import loadUi

from enmapbox import EnMAPBox
from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QMenu
from qgis.gui import QgsFileWidget


class ProcessingParameterPickleFileWidget(QWidget):
    mFile: QgsFileWidget
    mCreate: QToolButton
    mEdit: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(join(dirname(__file__), 'processingparameterpicklefilewidget.ui'), self)
        self.mEdit.hide()
        self.menu = QMenu()
        self.menu.setToolTipsVisible(True)

        if EnMAPBox.instance() is not None:
            self.menu.addSeparator()
            for filename in EnMAPBox.instance().dataSources('MODEL', True):
                if not filename.endswith('.pkl'):
                    continue
                action = self.menu.addAction(basename(filename))
                action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                action.setToolTip(rf'<html><head/><body><p>{filename}</p></body></html>')
                action.triggered.connect(self.onFilenameClicked)
                action.filename = filename

        self.mCreate.setMenu(self.menu)

    def value(self) -> str:
        return self.mFile.filePath()

    def setValue(self, value):
        self.mFile.setFilePath(value)

    filePath = value
    setFilePath = setValue

    def onFilenameClicked(self):
        filename = self.sender().filename
        self.mFile.setFilePath(filename)


class ProcessingParameterPickleFileWidgetWrapper(WidgetWrapper):
    widget: ProcessingParameterPickleFileWidget

    def createWidget(self):
        return ProcessingParameterPickleFileWidget()

    def setValue(self, value):
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()
