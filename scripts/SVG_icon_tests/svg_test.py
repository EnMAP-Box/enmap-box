from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon, QColor, QPalette
from qgis.PyQt.QtWidgets import QLabel, QGridLayout, QWidget
from qgis.testing import start_app

path = r'/Users/aryangoswami/Downloads/svg icon test/viewlist_textview_2nd.svg'

app = start_app()

icon = QIcon(path)

dark_palette = QPalette()

# Define dark theme colors
dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))


def addIcons(w: QWidget):
    l = QGridLayout()
    for i, size in enumerate([28, 64, 128, 256]):
        label1 = QLabel()
        label1.setPixmap(icon.pixmap(QSize(size, size)))
        label2 = QLabel(f'{size}x{size}px')
        l.addWidget(label1, 0, i)
        l.addWidget(label2, 1, i)
    w.setLayout(l)


w_bright = QWidget()
w_dark = QWidget()
w_dark.setPalette(dark_palette)

addIcons(w_bright)
addIcons(w_dark)
w_bright.show()
w_dark.show()
app.exec_()
