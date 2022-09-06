from qgis.PyQt.QtCore import QObject, pyqtSignal

class _Signals(QObject):
    fileCreated = pyqtSignal(str)
_signals = _Signals()
sigFileCreated = _signals.fileCreated

if __name__ == '__main__':

    def handler(filename):
        print(filename)

    sigFileCreated.connect(handler)
    sigFileCreated.emit('my.img')
