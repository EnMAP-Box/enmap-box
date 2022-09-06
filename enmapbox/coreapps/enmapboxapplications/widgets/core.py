from PyQt5.uic import loadUi
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

from enmapbox.gui.datasources.datasources import VectorDataSource
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.datasources.datasources import VectorDataSource
from _classic.hubflow.core import *

pathUi = join(dirname(__file__), 'ui')

class UiLibrary(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enmapBox = EnMAPBox.instance()
        assert isinstance(self.enmapBox, EnMAPBox)
        self.enmapBox.sigDataSourcesAdded.connect(self.setLibraries)

        self.names = list()
        self.filenames = list()
        self.setLibraries()
        self.setCurrentIndex(0)

    def setLibraries(self, *args, **kwargs):

        # add not selected item
        self.names.append('')
        self.filenames.append(None)
        self.addItem('')

        # add all speclibs
        for source in self.enmapBox.dataSourceManager().dataSources():
            if isinstance(source, VectorDataSource) and source.isSpectralLibrary():
                if source.uri() not in self.filenames:
                    self.names.append(source.mName)
                    self.filenames.append(source.uri())
                    self.addItem(self.names[-1])

    def currentLibrary(self):
        if self.currentIndex() >= 1 and self.currentIndex() < len(self.filenames):
            return EnviSpectralLibrary(filename=self.filenames[self.currentIndex()])
        else:
            return None

class UiLabeledLibrary(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi(join(pathUi, 'labeledLibary.ui'), self)
        #self.setupUi(self)
        self.uiLibrary().currentIndexChanged.connect(self.setFields)
        self.setFields(0)

    def setInfo(self, uiInfo):
        assert isinstance(uiInfo, QLabel)
        self.uiInfo_ = uiInfo

    def uiInfo(self):
        assert isinstance(self.uiInfo_, QLabel)
        return self.uiInfo_

    def uiLibrary(self):
        assert isinstance(self.uiLibrary_, UiLibrary)
        return self.uiLibrary_

    def uiField(self):
        assert isinstance(self.uiField_, QComboBox)
        return self.uiField_

    def setFields(self, index):
        for i in range(self.uiField().count()):
            self.uiField().removeItem(0)
        library = self.uiLibrary().currentLibrary()
        if library is not None:
            try:
                fields = library.attributeDefinitions()
                self.uiField().addItems(fields)
            except:
                import traceback
                self.uiInfo().setText(traceback.format_exc())

    def currentLibrary(self):
        return self.uiLibrary().currentLibrary()

    def currentField(self):
        text = self.uiField().currentText()
        if text == '':
            return None
        else:
            return text

class UiWorkflowMainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi(join(pathUi, 'main.ui'), self)
        #self.setupUi(self)

        self.uiRun().clicked.connect(self.run)
        self.uiCancel().clicked.connect(self.cancel)
        self.uiCancel().hide()

        self.worker = self.worker()
        self.worker.sigFinished.connect(self.onFinished)
        self.worker.sigProgressChanged.connect(self.onProgressChanged)
        self.worker.sigErrorRaised.connect(self.onError)

    def uiRun(self):
        obj = self.uiRun_
        assert isinstance(obj, QToolButton)
        return obj

    def uiCancel(self):
        obj = self.uiCancel_
        assert isinstance(obj, QToolButton)
        return obj

    def uiInfo(self):
        if not hasattr(self, 'uiInfo_'):
            self.uiInfo_ = QLabel()
            self.statusBar().addWidget(self.uiInfo_, 1)

        obj = self.uiInfo_
        assert isinstance(obj, QLabel)
        return obj

    def uiProgressBar(self):
        obj = self.uiProgressBar_
        assert isinstance(obj, QProgressBar)
        return obj

    def log(self, text):
        self.uiInfo().setText(str(text))
        QCoreApplication.processEvents()

    def run(self):

        if not self.worker.isRunning():
            self.log('Calculation started.')
            self.uiRun().hide()
            self.uiCancel().show()
            self.worker.start()
        else:
            self.log('Calculation is already running!')

    def cancel(self):
        if self.worker.isRunning():
            self.worker.terminate()
        self.uiProgressBar().setValue(0)
        self.uiRun().show()
        self.uiCancel().hide()

        self.log('Calculation canceled.')

    def onProgressChanged(self, percent):
        self.uiProgressBar().setValue(percent)

    def onError(self, error, tb):
        self.log('Error: {} (see log for details)'.format(error))
        print(tb)
        self.uiRun().show()
        self.uiCancel().hide()

    def onFinished(self, *args):
        self.uiProgressBar().setValue(0)
        self.uiRun().show()
        self.uiCancel().hide()

        self.log('Calculation finished.')
        #self.myWorker.quit()
        #self.myWorker.wait()
        #self.myWorker.terminate()

    def closeEvent(self, event):

        if not self.worker.isRunning():
            event.accept()  # let the window close
        else:
            self.log('Calculation still running!')
            event.ignore()

    def worker(self):
        raise NotImplementedError()
        return QThread()

class WorkflowWorker(QThread):
    sigProgressChanged = pyqtSignal(int)
    sigFinished = pyqtSignal()
    sigErrorRaised = pyqtSignal(Exception, str)

    def run(self):

        def progressCallback(percent):
            self.sigProgressChanged.emit(percent)

        try:
            self.run_(progressCallback)
        except Exception as error:
            import traceback
            tb = traceback.format_exc()
            self.sigErrorRaised.emit(error, tb)
            return

        self.sigFinished.emit()

    def run_(self, *args, **kwargs):
        pass