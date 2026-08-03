from os.path import basename, join, dirname

from enmapbox.gui.enmapboxgui import EnMAPBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QMenu
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMessageLog, Qgis
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetFactoryInterface, QgsGui
from qgis.gui import QgsFileWidget


class ProcessingParameterSkopsFileWidget(QWidget):
    mFile: QgsFileWidget
    mCreate: QToolButton
    mEdit: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(join(dirname(__file__), 'processingparameterskopsfilewidget.ui'), self)
        self.mEdit.hide()
        self.menu = QMenu()
        self.menu.setToolTipsVisible(True)

        if EnMAPBox.instance() is not None:
            self.menu.addSeparator()
            for filename in EnMAPBox.instance().dataSources('MODEL', True):
                if not filename.endswith('.skops'):
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


class ProcessingParameterSkopsFileWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):

    def createWidget(self):
        return ProcessingParameterSkopsFileWidget()

    def setWidgetValue(self, value, context):
        widget = self.wrappedWidget()
        widget.setValue(value)

    def widgetValue(self):
        widget = self.wrappedWidget()
        return widget.value()


class ProcessingParameterSkopsFileWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterSkopsFileWidget'

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        return ProcessingParameterSkopsFileWidgetWrapper(parameter, widget_type)

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)
