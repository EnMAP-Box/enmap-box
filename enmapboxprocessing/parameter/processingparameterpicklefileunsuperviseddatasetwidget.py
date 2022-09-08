from os.path import basename, join, dirname

from enmapbox import EnMAPBox
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromcodealgorithm import \
    PrepareUnsupervisedDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromfilealgorithm import \
    PrepareUnsupervisedDatasetFromFileAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromjsonalgorithm import \
    PrepareUnsupervisedDatasetFromJsonAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromlibraryalgorithm import \
    PrepareUnsupervisedDatasetFromLibraryAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromrasteralgorithm import \
    PrepareUnsupervisedDatasetFromRasterAlgorithm
from enmapboxprocessing.algorithm.prepareunsuperviseddatasetfromvectorandfieldsalgorithm import \
    PrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm
from enmapboxprocessing.typing import TransformerDump
from enmapboxprocessing.utils import Utils
from processing import AlgorithmDialog
from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QMenu, QMessageBox
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsFileWidget


class ProcessingParameterPickleFileUnsupervisedDatasetWidget(QWidget):
    mFile: QgsFileWidget
    mCreate: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(join(dirname(__file__), 'processingparameterpicklefilewidget.ui'), self)

        self.menu = QMenu()
        self.menu.setToolTipsVisible(True)

        for alg, icon in [
            (PrepareUnsupervisedDatasetFromRasterAlgorithm(),
             QIcon(':/images/themes/default/mIconRaster.svg')),

            (PrepareUnsupervisedDatasetFromVectorAndFieldsAlgorithm(),
             QIcon(':/images/themes/default/mActionOpenTable.svg')),

            (PrepareUnsupervisedDatasetFromLibraryAlgorithm(),
             QIcon(':/qps/ui/icons/speclib.svg')),

            (PrepareUnsupervisedDatasetFromCodeAlgorithm(),
             QIcon(':/images/themes/default/mIconPythonFile.svg')),

            (PrepareUnsupervisedDatasetFromFileAlgorithm(),
             QIcon(':/images/themes/default/mIconFile.svg')),

            (PrepareUnsupervisedDatasetFromJsonAlgorithm(),
             QIcon(':/images/themes/default/mIconFieldJson.svg'))
        ]:
            action = self.menu.addAction(alg.displayName())
            action.setIcon(icon)
            action.setText(alg.displayName())
            action.triggered.connect(self.onCreateClicked)
            action.alg = alg

        if EnMAPBox.instance() is not None:
            self.menu.addSeparator()
            for filename in EnMAPBox.instance().dataSources('MODEL', True):
                if not filename.endswith('.pkl'):
                    continue
                try:
                    dump = TransformerDump(**Utils.pickleLoad(filename))
                    samples, features = dump.X.shape
                except Exception:
                    continue

                action = self.menu.addAction('')
                action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                action.setText(basename(filename) + f' ({samples} samples, {features} features)')
                action.setToolTip(rf'<html><head/><body><p>{filename}</p></body></html>')
                action.triggered.connect(self.onFilenameClicked)
                action.filename = filename

        self.mCreate.setMenu(self.menu)

    def value(self) -> str:
        return self.mFile.filePath()

    def setValue(self, value):
        self.mFile.setFilePath(value)

    filePath = value
    setFilePath = setValue

    def onCreateClicked(self):
        from enmapbox import EnMAPBox
        enmapBox = EnMAPBox.instance()

        class AlgorithmDialogWrapper(AlgorithmDialog):
            def finish(self_, successful, result, context, feedback, in_place=False):
                super().finish(successful, result, context, feedback, in_place)
                if successful:
                    filename = result['outputUnsupervisedDataset']
                    self.mFile.setFilePath(filename)

                    dump = TransformerDump(**Utils.pickleLoad(filename))
                    samples, features = dump.X.shape

                    # add to the list!
                    action = self.menu.addAction(alg.displayName())
                    action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                    action.setText(basename(filename) + f' ({samples} samples, {features} features)')
                    action.setToolTip(rf'<html><head/><body><p>{filename}</p></body></html>')
                    action.triggered.connect(self.onFilenameClicked)
                    action.filename = filename

                    self_.close()

        alg = self.sender().alg
        if enmapBox is None:
            QMessageBox.information(self, 'Information', 'EnMAP-Box not running.')
            return

        enmapBox.showProcessingAlgorithmDialog(alg, modal=True, wrapper=AlgorithmDialogWrapper, parent=self)

    def onFilenameClicked(self):
        filename = self.sender().filename
        self.mFile.setFilePath(filename)


class ProcessingParameterPickleFileUnsupervisedDatasetWidgetWrapper(WidgetWrapper):
    widget: ProcessingParameterPickleFileUnsupervisedDatasetWidget

    def createWidget(self):
        return ProcessingParameterPickleFileUnsupervisedDatasetWidget()

    def setValue(self, value):
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()
