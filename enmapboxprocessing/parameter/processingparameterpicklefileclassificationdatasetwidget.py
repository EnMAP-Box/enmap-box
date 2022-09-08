from os.path import basename, join, dirname

from enmapboxprocessing.algorithm.prepareclassificationdatasetfromjsonalgorithm import \
    PrepareClassificationDatasetFromJsonAlgorithm
from qgis.PyQt.uic import loadUi

from enmapbox import EnMAPBox
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedlibraryalgorithm import \
    PrepareClassificationDatasetFromCategorizedLibraryAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedrasteralgorithm import \
    PrepareClassificationDatasetFromCategorizedRasterAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedvectoralgorithm import \
    PrepareClassificationDatasetFromCategorizedVectorAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedvectorandfieldsalgorithm import \
    PrepareClassificationDatasetFromCategorizedVectorAndFieldsAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcodealgorithm import \
    PrepareClassificationDatasetFromCodeAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromfilesalgorithm import \
    PrepareClassificationDatasetFromFilesAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromtablealgorithm import \
    PrepareClassificationDatasetFromTableAlgorithm
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from processing import AlgorithmDialog
from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QMenu, QMessageBox
from qgis.gui import QgsFileWidget


class ProcessingParameterPickleFileClassificationDatasetWidget(QWidget):
    mFile: QgsFileWidget
    mCreate: QToolButton
    mEdit: QToolButton

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(join(dirname(__file__), 'processingparameterpicklefilewidget.ui'), self)

        self.menu = QMenu()
        self.menu.setToolTipsVisible(True)

        for alg, icon in [
            (PrepareClassificationDatasetFromCategorizedVectorAlgorithm(),
             QIcon(':/images/themes/default/mIconVector.svg')),

            (PrepareClassificationDatasetFromCategorizedRasterAlgorithm(),
             QIcon(':/enmapbox/gui/ui/icons/filelist_classification.svg')),

            (PrepareClassificationDatasetFromCategorizedLibraryAlgorithm(),
             QIcon(':/qps/ui/icons/speclib.svg')),

            (PrepareClassificationDatasetFromCategorizedVectorAndFieldsAlgorithm(),
             QIcon(':/images/themes/default/mActionOpenTable.svg')),

            (PrepareClassificationDatasetFromTableAlgorithm(),
             QIcon(':/images/themes/default/mActionOpenTable.svg')),

            (PrepareClassificationDatasetFromCodeAlgorithm(),
             QIcon(':/images/themes/default/mIconPythonFile.svg')),

            (PrepareClassificationDatasetFromFilesAlgorithm(),
             QIcon(':/images/themes/default/mIconFile.svg')),

            (PrepareClassificationDatasetFromJsonAlgorithm(),
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
                    dump = ClassifierDump(**Utils.pickleLoad(filename))
                    samples, features = dump.X.shape
                    classes = len(dump.categories)
                except Exception:
                    continue

                action = self.menu.addAction(alg.displayName())
                action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                action.setText(basename(filename) + f' ({samples} samples, {features} features, {classes} classes)')
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
        from enmapbox import EnMAPBox
        enmapBox = EnMAPBox.instance()

        class AlgorithmDialogWrapper(AlgorithmDialog):
            def finish(self_, successful, result, context, feedback, in_place=False):
                super().finish(successful, result, context, feedback, in_place)
                if successful:
                    filename = result['outputClassificationDataset']
                    self.mFile.setFilePath(filename)

                    dump = ClassifierDump(**Utils.pickleLoad(filename))
                    samples, features = dump.X.shape
                    classes = len(dump.categories)

                    # add to the list!
                    action = self.menu.addAction(alg.displayName())
                    action.setIcon(QIcon(':/images/themes/default/mIconFile.svg'))
                    action.setText(basename(filename) + f' ({samples} samples, {features} features, {classes} classes)')
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
        from classificationdatasetmanagerapp import ClassificationDatasetManagerGui
        self.dialog = ClassificationDatasetManagerGui(self)
        self.dialog.mDataset.mFile.setFilePath(filename)
        self.dialog.exec_()
        filename = self.dialog.mDataset.mFile.filePath()

        QMessageBox.information(self, 'Classification Dataset Manager', f'Update dataset file {basename(filename)}.')
        self.mFile.setFilePath(filename)


class ProcessingParameterPickleFileClassificationDatasetWidgetWrapper(WidgetWrapper):
    widget: ProcessingParameterPickleFileClassificationDatasetWidget

    def createWidget(self):
        return ProcessingParameterPickleFileClassificationDatasetWidget()

    def setValue(self, value):
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()
