import json

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QVBoxLayout, QScrollArea

import requests
from enmapbox.typeguard import typechecked
from newsapp.newsitemwidget import NewsItemWidget
from qgis.PyQt import uic
from qgis.gui import QgsDockWidget


@typechecked
class NewsDockWidget(QgsDockWidget):
    mMessages: QScrollArea
    mLayout: QVBoxLayout

    def __init__(self, parent=None):
        QgsDockWidget.__init__(self, parent)
        uic.loadUi(__file__.replace('.py', '.ui'), self)

    def addItems(self):
        newsUrl = r'https://raw.githubusercontent.com/EnMAP-Box/enmap-box-documentation/main/NEWS.json'

        try:
            text = requests.get(newsUrl).text
            newsList = json.loads(text)
        except Exception:
            self.hide()
            return

        foundNoCurrentNewsItem = True
        for newsItem in reversed(newsList):
            dateEnd = QDate(*map(int, newsItem['date_end'].split('-')))  # parses dates like "2025-05-01"
            if QDate.currentDate() <= dateEnd:
                w = NewsItemWidget(
                    newsItem['title'], newsItem['message'], newsItem['image'], newsItem['url']
                )
                self.mLayout.insertWidget(0, w)
                foundNoCurrentNewsItem = False

        if foundNoCurrentNewsItem:
            self.hide()
