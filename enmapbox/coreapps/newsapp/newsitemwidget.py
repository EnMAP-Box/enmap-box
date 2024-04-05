import webbrowser

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QTextEdit, QWidget, QToolButton

import requests
from enmapbox.typeguard import typechecked
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QLabel


@typechecked
class NewsItemWidget(QWidget):
    mImage: QLabel
    mTitle: QLabel
    mText: QTextEdit
    mUrl: QToolButton

    def __init__(self, title: str, text: str, imageUrl: str, webUrl: str, parent=None):
        QLabel.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

        self.mTitle.setText(title)
        self.mText.setText(text)

        image = QImage()
        image.loadFromData(requests.get(imageUrl).content)
        image = image.scaled(self.mImage.size(), Qt.KeepAspectRatio)
        self.mImage.setPixmap(QPixmap(image))

        self.mUrl.triggered.connect(lambda: webbrowser.open_new(webUrl))