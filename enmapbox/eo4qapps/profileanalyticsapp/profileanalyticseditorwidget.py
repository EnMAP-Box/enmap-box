from enmapbox.gui.widgets.codeeditwidget import CodeEditWidget
from qgis.PyQt.QtWidgets import QWidget, QMainWindow, QToolButton, QLabel, QTextEdit
from qgis.PyQt.uic import loadUi
from enmapboxexternal.typeguard import typechecked


@typechecked
class ProfileAnalyticsEditorWidget(QMainWindow):
    mFilename: QLabel
    mCode: CodeEditWidget
    mLog: QTextEdit
    mSave: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.mSave.clicked.connect(self.onSaveClicked)

    def onSaveClicked(self):
        filename = self.mFilename.text()
        with open(filename, 'w') as file:
            file.write(self.mCode.text())
