import os

from enmapbox.gui.dataviews.docks import Dock
from qgis.PyQt.QtCore import QUrl


class WebViewDock(Dock):
    def __init__(self, *args, **kwargs):
        uri = kwargs.pop('uri', None)
        url = kwargs.pop('url', None)
        super(WebViewDock, self).__init__(*args, **kwargs)
        # self.setLineWrapMode(QTextEdit.FixedColumnWidth)

        from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
        self.webView = QWebEngineView(self)
        self.layout.addWidget(self.webView)

        if uri is not None:
            self.load(uri)
        elif url is not None:
            self.load(url)

    def showHtml(self, html: str):
        self.webView.setHtml(html)

    def load(self, uri):
        if os.path.isfile(uri):
            url = QUrl.fromLocalFile(uri)
        else:
            url = QUrl(uri)
        self.webView.load(url)

        if False:
            settings = self.webView.page().settings()
            # from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
            from qgis.PyQt.QtWebEngineCore import QWebEngineSettings
            WA = QWebEngineSettings.WebAttribute
            settings.setAttribute(WA.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(WA.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(WA.LocalStorageEnabled, True)
            settings.setAttribute(WA.AutoLoadImages, True)
