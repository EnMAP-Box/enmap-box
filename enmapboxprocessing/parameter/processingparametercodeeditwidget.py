from qgis.PyQt.Qsci import QsciScintilla, QsciLexerPython
from qgis.PyQt.uic import loadUi

from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtGui import QFont, QFontMetrics, QColor
from qgis.PyQt.QtWidgets import QWidget


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
        self.setMarginWidth(0, fontmetrics.width("000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#e3e3e3"))

    #        self.setMinimumSize(0, 300)

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


class ProcessingParameterCodeEditWidgetWrapper(WidgetWrapper):
    # adopted from C:\source\QGIS3-master\python\plugins\processing\algs\gdal\ui\RasterOptionsWidget.py

    widget: ProcessingParameterCodeEdit

    def createWidget(self):
        # if self.dialogType == DIALOG_MODELER:
        #    return ProcessingParameterCodeEdit()
        # elif self.dialogType == DIALOG_BATCH:
        #    raise NotImplementedError()
        # else:
        return ProcessingParameterCodeEdit()

    def setValue(self, value):
        # if self.dialogType == DIALOG_MODELER:
        #    raise NotImplementedError()
        # elif self.dialogType == DIALOG_BATCH:
        #    raise NotImplementedError()
        # else:
        self.widget.codeEdit.setText(value)

    def value(self):
        # if self.dialogType == DIALOG_MODELER:
        #    raise NotImplementedError()
        # elif self.dialogType == DIALOG_BATCH:
        #    raise NotImplementedError()
        # else:
        return self.widget.codeEdit.value()
