from os.path import splitext

from enmapbox.qgispluginsupport.qps.resources import showResources
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMainWindow, QListWidget, QListWidgetItem, QLineEdit, QComboBox
from qgis.PyQt.uic import loadUi
from enmapboxexternal.typeguard import typechecked


@typechecked
class ResourceGalleryDialog(QMainWindow):
    mList: QListWidget
    mPath: QLineEdit
    mSize: QComboBox

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        browser = showResources()
        browser.hide()
        model = browser.tableView.model()
        for row in range(model.rowCount()):
            path = model.index(row, 0).data()
            if splitext(path)[1] not in ['.svg', '.png']:
                continue
            item = QListWidgetItem(QIcon(path), '')
            item.path = path
            self.mList.addItem(item)

        self.mList.itemSelectionChanged.connect(self.onSelectionChanged)
        self.mSize.currentIndexChanged.connect(self.onSizeChanged)

    def onSelectionChanged(self):
        item = self.mList.currentItem()
        self.mPath.setText(item.path)

    def onSizeChanged(self):
        size = int(self.mSize.currentText())
        self.mList.setIconSize(QSize(size, size))
