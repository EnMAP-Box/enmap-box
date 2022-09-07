from typing import List, Tuple

from enmapboxprocessing.parameter.processingparametercodeeditwidget import CodeEditWidget
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QLineEdit
from typeguard import typechecked


class DialogUi(object):
    def setupUi(self, dialog):
        dialog.resize(600, 400)

        vbox = QVBoxLayout()
        dialog.setLayout(vbox)
        i = 1
        for rasterName in dialog.rasterNames:
            if rasterName in dialog.code:
                vbox.addWidget(QLabel(f'Select placeholder for source "{rasterName}"'))
                mPlaceholder = QLineEdit('raster' + str(i))
                mPlaceholder.textChanged.connect(dialog.onPlaceholderChanged)
                vbox.addWidget(mPlaceholder)
                dialog.placeholders.append((mPlaceholder, rasterName))

        vbox.addWidget(QLabel('Code snippet preview'))
        self.mSnippet = CodeEditWidget()
        self.mSnippet.setReadOnly(False)
        vbox.addWidget(self.mSnippet)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(dialog.accept)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(dialog.close)
        vbox.addWidget(self.buttonBox)


@typechecked
class SnippetSaveAsDialog(QDialog, DialogUi):
    mSnippet: CodeEditWidget
    placeholders: List[Tuple[QLineEdit, str]]

    def __init__(self, code: str, rasterNames: List[str], parent=None):
        QDialog.__init__(self, parent)
        self.code = code
        self.rasterNames = rasterNames
        self.placeholders = list()
        self.setupUi(self)
        self.setWindowTitle('Select placeholders')
        self.onPlaceholderChanged()

    def onPlaceholderChanged(self):
        snippet = self.code
        for mPlaceholder, rasterName in self.placeholders:
            placeholder = mPlaceholder.text()
            if placeholder == '':
                continue
            placeholder = Utils.makeIdentifier(placeholder)
            snippet = snippet.replace(rasterName, '{' + placeholder + '}')

        self.mSnippet.setReadOnly(False)
        self.mSnippet.setText(snippet)
        self.mSnippet.setReadOnly(True)

    def values(self):
        placeholders = dict()
        for mPlaceholder, rasterName in self.placeholders:
            placeholder = mPlaceholder.text()
            if placeholder == '':
                continue
            placeholders[Utils.makeIdentifier(placeholder)] = 'QgsRasterLayer'

        snippet = str(placeholders) + '\n'
        snippet += self.mSnippet.text()
        return snippet
