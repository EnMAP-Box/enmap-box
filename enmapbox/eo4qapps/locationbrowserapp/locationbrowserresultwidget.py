from PyQt5.QtWidgets import QListWidget, QTextEdit, QCheckBox, QToolButton

from qgis.PyQt.QtWidgets import QWidget, QMainWindow
from qgis.PyQt.uic import loadUi
from typeguard import typechecked


@typechecked
class LocationBrowserResultWidget(QMainWindow):
    mList: QListWidget
    mDetails: QTextEdit
    mLiveUpdate: QCheckBox
    mApply: QToolButton
    mZoomToSelection: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)
