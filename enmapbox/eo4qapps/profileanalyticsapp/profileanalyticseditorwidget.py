from enmapbox.gui.widgets.codeeditwidget import CodeEditWidget
from enmapbox.typeguard import typechecked
from qgis.PyQt.QtWidgets import QMainWindow, QToolButton, QLabel, QTextEdit
from qgis.PyQt.uic import loadUi


@typechecked
class ProfileAnalyticsEditorWidget(QMainWindow):
    mFilename: QLabel
    mCode: CodeEditWidget
    mLog: QTextEdit
    mSave: QToolButton

    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.mSave.clicked.connect(self.onSaveClicked)

    def onSaveClicked(self):
        filename = self.mFilename.text()
        with open(filename, 'w') as file:
            file.write(self.mCode.text())
