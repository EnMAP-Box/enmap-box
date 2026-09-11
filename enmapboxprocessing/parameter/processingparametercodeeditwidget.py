from qgis.PyQt import sip
from qgis.PyQt.Qsci import QsciScintilla, QsciLexerPython
from qgis.PyQt.QtGui import QFont, QFontMetrics, QColor
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMessageLog, Qgis
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetFactoryInterface, QgsGui


class CodeEditWidget(QsciScintilla):
    def __init__(self, parent=None):
        QsciScintilla.__init__(self, parent)
        self.setLexer(QsciLexerPython(self))

        # Set the default font
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPixelSize(8)

        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.boundingRect("000").width() + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#e3e3e3"))

    def setToolTip(self, *args, **kwargs):
        pass

    def value(self):
        return self.text()


class ProcessingParameterCodeEdit(QWidget):
    codeEdit: CodeEditWidget

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)
        self.codeEdit.setMinimumSize(0, 300)


class ProcessingParameterCodeEditWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget = None

    def createWidget(self):
        self._widget = ProcessingParameterCodeEdit()
        return self._widget

    def setWidgetValue(self, value, context):
        if self._widget is not None:
            self._widget.codeEdit.setText(value)
        else:
            widget = self.wrappedWidget()
            if widget is not None:
                widget.codeEdit.setText(value)

    def widgetValue(self):
        if self._widget is not None:
            return self._widget.codeEdit.value()
        widget = self.wrappedWidget()
        if widget is not None:
            return widget.codeEdit.value()
        return None


class ProcessingParameterCodeEditWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterCodeEditWidget'
    _wrappers = []

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        wrapper = ProcessingParameterCodeEditWidgetWrapper(parameter, widget_type)
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
