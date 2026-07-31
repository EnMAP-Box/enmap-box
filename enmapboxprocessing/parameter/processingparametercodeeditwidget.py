from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetFactoryInterface, QgsGui

from qgis.PyQt.Qsci import QsciScintilla, QsciLexerPython
from qgis.PyQt.QtGui import QFont, QFontMetrics, QColor
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.uic import loadUi


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

    def __init__(self, parameter, widget_type, parent=None):
        super().__init__(parameter, widget_type, parent)

    def createWidget(self):
        widget = ProcessingParameterCodeEdit()
        return widget

    def setWidgetValue(self, value, context):
        widget = self.wrappedWidget()
        widget.codeEdit.setText(value)

    def widgetValue(self):
        widget = self.wrappedWidget()
        return widget.codeEdit.value()


class ProcessingParameterCodeEditWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterCodeEditWidget'

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        return ProcessingParameterCodeEditWidgetWrapper(parameter, widget_type)

    @classmethod
    def register(cls):
        QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
