
from qgis.PyQt.QtWidgets import QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QLabel
from qgis.gui import QgsCollapsibleGroupBox
from qgis.testing import start_app

app = start_app()

gb = QgsCollapsibleGroupBox()
label1 = QLabel('Visible')
label2 = QLabel('Invisible')
label2.setVisible(False)

hbox = QHBoxLayout()
hbox.addWidget(label1)
hbox.addWidget(label2)

if False:
    gb.setLayout(hbox)
else:
    # workaround: wrap layout with QWidget
    # wrap with frame
    frame = QWidget()
    frame.setLayout(hbox)
    gb.setLayout(QVBoxLayout())
    gb.layout().addWidget(frame)


w = QWidget()
layout = QVBoxLayout()
layout.addWidget(gb)
# space item to compress the collapsible group box
layout.addSpacerItem(QSpacerItem(0, 0, vPolicy=QSizePolicy.Expanding))
w.setLayout(layout)
w.show()

gb.setCollapsed(True)
gb.setCollapsed(False)

assert label1.isVisible()
assert not label2.isVisible()


app.exec_()
