from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap, QColor
from qgis.PyQt.QtWidgets import QSplashScreen, QGraphicsDropShadowEffect, QApplication

PATH_SPLASHSCREEN = Path(__file__).parent / 'splashscreen.png'


class EnMAPBoxSplashScreen(QSplashScreen):
    """
    Thr EnMAP-Box Splash Screen
    """

    def __init__(self, parent=None):
        pm = QPixmap(PATH_SPLASHSCREEN.as_posix())
        super(EnMAPBoxSplashScreen, self).__init__(parent, pixmap=pm)

        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(5)
        effect.setColor(QColor('white'))
        self.setGraphicsEffect(effect)

        css = "" \
              ""

    def showMessage(self, text: str, alignment: Qt.Alignment = None, color: QColor = None):
        """
        Shows a message
        :param text:
        :param alignment:
        :param color:
        :return:
        """
        if alignment is None:
            alignment = int(Qt.AlignLeft | Qt.AlignBottom)
        if color is None:
            color = QColor('black')
        super(EnMAPBoxSplashScreen, self).showMessage(text, alignment, color)
        QApplication.processEvents()

    """
    def drawContents(self, painter: QPainter) -> None:
        # color = QColor('black')
        color = QColor('white')
        color.setAlpha(125)

        painter.setBrush(color)
        painter.setPen(color)
        size = self.size()
        h = 25
        d = 10
        rect = QRect(QRect(0, size.height()-h-d, size.width(), size.height()-d) )
        painter.drawRect(rect)
        #painter.setPen(QColor('white'))
        super().drawContents(painter)
    """
