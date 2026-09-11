from os.path import basename, join, dirname

from enmapbox.gui.enmapboxgui import EnMAPBox
from qgis.PyQt import sip
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget = None

    def createWidget(self):
        self._widget = ProcessingParameterSkopsFileWidget()
        return self._widget

    def setWidgetValue(self, value, context):
        if self._widget is not None:
            self._widget.setValue(value)
        else:
            widget = self.wrappedWidget()
            if widget is not None:
                widget.setValue(value)

    def widgetValue(self):
        if self._widget is not None:
            return self._widget.value()
        widget = self.wrappedWidget()
        if widget is not None:
            return widget.value()
        return None


class ProcessingParameterSkopsFileWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterSkopsFileWidget'
    _wrappers = []

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        wrapper = ProcessingParameterSkopsFileWidgetWrapper(parameter, widget_type)
        sip.transferto(wrapper, None)
        self._wrappers.append(wrapper)
        return wrapper

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)
