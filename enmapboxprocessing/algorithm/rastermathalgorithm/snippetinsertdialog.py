from typing import List

from enmapboxprocessing.parameter.processingparametercodeeditwidget import CodeEditWidget
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QComboBox, QLabel, QVBoxLayout
from qgis.core import QgsRasterLayer
from typeguard import typechecked


class DialogUi(object):
    def setupUi(self, dialog):
        dialog.resize(600, 400)

        vbox = QVBoxLayout()
        dialog.setLayout(vbox)
        for placeholder, type in dialog.inputs.items():
            vbox.addWidget(QLabel(f'Select source for placeholder "{placeholder}"'))
            comboBox = QComboBox()
            comboBox.addItems([''] + dialog.rasterNames)
            comboBox.currentIndexChanged.connect(dialog.onIndexChanged)
            vbox.addWidget(comboBox)
            dialog.sources.append((comboBox, placeholder))

        vbox.addWidget(QLabel('Code snippet preview'))
        self.mCode = CodeEditWidget()
        self.mCode.setText(dialog.code)
        self.mCode.setReadOnly(True)
        vbox.addWidget(self.mCode)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(dialog.accept)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(dialog.close)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        vbox.addWidget(self.buttonBox)


@typechecked
class SnippetInsertDialog(QDialog, DialogUi):
    sources: List
    mCode: CodeEditWidget

    def __init__(self, snippet: str, rasterNames: List[str], parent=None):
        QDialog.__init__(self, parent)
        self.snippet = snippet
        self.rasterNames = rasterNames
        lines = snippet.strip().splitlines()
        self.inputs = eval(lines[0], {'QgsRasterLayer': QgsRasterLayer})
        self.code = '\n'.join(lines[1:]).strip()
        self.sources = list()

        self.setupUi(self)
        self.setWindowTitle('Select sources')

    def onIndexChanged(self):
        code = self.code
        for comboBox, identifier in self.sources:
            if comboBox.currentText() == '':
                continue
            code = code.replace('{' + identifier + '}', comboBox.currentText())

        self.mCode.setReadOnly(False)
        self.mCode.setText(code)
        self.mCode.setReadOnly(True)
        self.updateOkButton()

    def updateOkButton(self):
        for comboBox, identifier in self.sources:
            if comboBox.currentText() == '':
                self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
                return
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def values(self):
        return self.mCode.text()
