from qgis.PyQt.Qsci import QsciScintilla, QsciLexerPython
from qgis.PyQt.QtGui import QFont, QFontMetrics, QColor


class CodeEditWidget(QsciScintilla):
    def __init__(self, parent=None):
        QsciScintilla.__init__(self, parent)
        self.setLexer(QsciLexerPython(self))

        # Set the default font
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        # font.setPointSize(10)
        font.setPixelSize(8)

        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#e3e3e3"))
