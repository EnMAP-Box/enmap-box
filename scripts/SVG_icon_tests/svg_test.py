from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon, QColor, QPalette
from qgis.PyQt.QtWidgets import QLabel, QGridLayout, QWidget
from qgis.testing import start_app

path = r'/Users/aryangoswami/Downloads/svg icon test/viewlist_textview_2nd.svg'

app = start_app()

icon = QIcon(path)

dark_palette = QPalette()

# Define dark theme colors
dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))


def addIcons(w: QWidget):
    layout = QGridLayout()
    for i, size in enumerate([28, 64, 128, 256]):
        label1 = QLabel()
        label1.setPixmap(icon.pixmap(QSize(size, size)))
        label2 = QLabel(f'{size}x{size}px')
        layout.addWidget(label1, 0, i)
        layout.addWidget(label2, 1, i)
    w.setLayout(layout)


w_bright = QWidget()
w_dark = QWidget()
w_dark.setPalette(dark_palette)

addIcons(w_bright)
addIcons(w_dark)
w_bright.show()
w_dark.show()
app.exec()
