from qgis.PyQt.QtWidgets import QApplication, QMenu, QWidget, QVBoxLayout, QLabel, QPushButton

app = QApplication([])


def myFunctionA():
    print('Function A called')


def myFunctionB(*args):
    print('Function B arguments: {}'.format(args))


menu = QMenu()
a = menu.addAction('Do this')
a.triggered.connect(myFunctionA)

a = menu.addAction('Do that')
a.triggered.connect(lambda: myFunctionB(0, 8, 15))

menu.show()


def onButtonClicked():
    print('Button was pressed')


w = QWidget()
w.setLayout(QVBoxLayout())
w.layout().addWidget(QLabel('Hello World'))
btn = QPushButton()
btn.setText('click me')
btn.clicked.connect(onButtonClicked)
w.layout().addWidget(btn)
w.layout().addWidget(QLabel('(and check your command line)'))
w.show()

app.exec()
