from os.path import basename, join, dirname

from enmapboxprocessing.algorithm.prepareregressiondatasetfromjsonalgorithm import \
    PrepareRegressionDatasetFromJsonAlgorithm
from qgis.PyQt.uic import loadUi

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcodealgorithm import \
    PrepareRegressionDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuouslibraryalgorithm import \
    PrepareRegressionDatasetFromContinuousLibraryAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousrasteralgorithm import \
    PrepareRegressionDatasetFromContinuousRasterAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectoralgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromcontinuousvectorandfieldsalgorithm import \
    PrepareRegressionDatasetFromContinuousVectorAndFieldsAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromfilesalgorithm import \
    PrepareRegressionDatasetFromFilesAlgorithm
from enmapboxprocessing.algorithm.prepareregressiondatasetfromtablealgorithm import \
    PrepareRegressionDatasetFromTableAlgorithm
from enmapboxprocessing.typing import RegressorDump
from enmapboxprocessing.utils import Utils
from processing import AlgorithmDialog
from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QMenu, QMessageBox
from qgis.gui import QgsFileWidget


class ProcessingParameterPickleFileRegressionDatasetWidget(QWidget):
    mFile: QgsFileWidget
    mCreate: QToolButton
    mEdit: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(join(dirname(__file__), 'processingparameterpicklefilewidget.ui'), self)

        self.menu = QMenu()
        self.menu.setToolTipsVisible(True)

        for alg, icon in [
            (PrepareRegressionDatasetFromContinuousVectorAlgorithm(),
             QIcon(':/images/themes/default/mIconVector.svg')),

            (PrepareRegressionDatasetFromContinuousRasterAlgorithm(),
             QIcon(':/images/themes/default/algorithms/mAlgorithmRandomRaster.svg')),

            (PrepareRegressionDatasetFromContinuousLibraryAlgorithm(),
             QIcon(':/qps/ui/icons/speclib.svg')),

            (PrepareRegressionDatasetFromContinuousVectorAndFieldsAlgorithm(),
             QIcon(':/images/themes/default/mActionOpenTable.svg')),

            (PrepareRegressionDatasetFromTableAlgorithm(),
             QIcon(':/images/themes/default/mActionOpenTable.svg')),

            (PrepareRegressionDatasetFromCodeAlgorithm(),
             QIcon(':/images/themes/default/mIconPythonFile.svg')),

            (PrepareRegressionDatasetFromFilesAlgorithm(),
             QIcon(':/images/themes/default/mIconFile.svg')),

            (PrepareRegressionDatasetFromJsonAlgorithm(),
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
                    dump = RegressorDump.fromDict(Utils.pickleLoad(filename))
                    samples, features = dump.X.shape
                    targets = len(dump.targets)
                except Exception:
                    continue

                action = self.menu.addAction('')
                action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                action.setText(basename(filename) + f' ({samples} samples, {features} features, {targets} targets)')
                action.setToolTip(rf'<html><head/><body><p>{filename}</p></body></html>')
                action.triggered.connect(self.onFilenameClicked)
                action.filename = filename

        self.mCreate.setMenu(self.menu)
        self.mEdit.clicked.connect(self.onEditClicked)

    def value(self) -> str:
        return self.mFile.filePath()

    def setValue(self, value):
        self.mFile.setFilePath(value)

    filePath = value
    setFilePath = setValue

    def onCreateClicked(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox.instance()

        class AlgorithmDialogWrapper(AlgorithmDialog):
            def finish(self_, successful, result, context, feedback, in_place=False):
                super().finish(successful, result, context, feedback, in_place)
                if successful:
                    filename = result['outputRegressionDataset']
                    self.mFile.setFilePath(filename)

                    dump = RegressorDump.fromDict(Utils.pickleLoad(filename))
                    samples, features = dump.X.shape
                    targets = len(dump.targets)

                    # add to the list!
                    action = self.menu.addAction(alg.displayName())
                    action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                    action.setText(basename(filename) + f' ({samples} samples, {features} features, {targets} targets)')
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

    def onEditClicked(self):
        filename = self.mFile.filePath()
        from regressiondatasetmanagerapp import RegressionDatasetManagerGui
        self.dialog = RegressionDatasetManagerGui(self)
        self.dialog.mDataset.mFile.setFilePath(filename)
        self.dialog.exec_()
        filename = self.dialog.mDataset.mFile.filePath()

        QMessageBox.information(self, 'Regression Dataset Manager', f'Update dataset file {basename(filename)}.')
        self.mFile.setFilePath(filename)


class ProcessingParameterPickleFileRegressionDatasetWidgetWrapper(WidgetWrapper):
    widget: ProcessingParameterPickleFileRegressionDatasetWidget

    def createWidget(self):
        return ProcessingParameterPickleFileRegressionDatasetWidget()

    def setValue(self, value):
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()
