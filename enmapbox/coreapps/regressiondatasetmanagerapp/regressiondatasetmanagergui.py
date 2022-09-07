from os.path import basename, join

from enmapboxprocessing.algorithm.randomsamplesfromregressiondatasetalgorithm import \
    RandomSamplesFromRegressionDatasetAlgorithm
from enmapboxprocessing.parameter.processingparameterpicklefileregressiondatasetwidget import \
    ProcessingParameterPickleFileRegressionDatasetWidget
from enmapboxprocessing.typing import RegressorDump, Target
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem, QLabel, QToolButton, QMessageBox,
                                 QComboBox,
                                 QDialog)
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsColorButton
from typeguard import typechecked


@typechecked
class RegressionDatasetManagerGui(QDialog):
    mDataset: ProcessingParameterPickleFileRegressionDatasetWidget
    mTargetTable: QTableWidget
    mFeaturesTable: QTableWidget
    mRestore: QToolButton
    mSave: QToolButton
    mSampleType: QComboBox
    mRandomSample: QToolButton

    RelativeSampling, AbsoluteSampling = 0, 1

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        self.mDataset.mEdit.hide()

        self.mDataset.mFile.fileChanged.connect(self.onDatasetChanged)
        self.mRestore.clicked.connect(self.onRestoreClicked)
        self.mSave.clicked.connect(self.onSaveClicked)
        self.mRandomSample.clicked.connect(self.onRandomSampleClicked)

    def currentEdits(self):
        filename = self.mDataset.mFile.filePath()
        try:
            dump = RegressorDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            return

        sizes = list()
        targets = list()
        for row in range(self.mTargetTable.rowCount()):
            w: QTableWidgetItem = self.mTargetTable.item(row, 0)
            name = w.text()
            w: QgsColorButton = self.mTargetTable.cellWidget(row, 1)
            color = w.color().name()
            targets.append(Target(name, color))
            w: QLabel = self.mTargetTable.cellWidget(row, 2)
            size = int(w.text().split(' ')[0])
            sizes.append(size)

        features = list()
        for row in range(self.mFeaturesTable.rowCount()):
            w: QTableWidgetItem = self.mFeaturesTable.item(row, 0)
            name = w.text()
            features.append(name)

        return targets, features, sizes

    def onRestoreClicked(self, *args):
        self.onDatasetChanged()

    def onSaveClicked(self, *args, question=True):
        filename = self.mDataset.mFile.filePath()
        try:
            dump = RegressorDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            return

        if question:
            button = QMessageBox.question(
                self, 'Save Edits', f'Do you want to save the changes to file {basename(filename)}?'
            )
            if button == QMessageBox.No:
                return

        targets, features, sizes = self.currentEdits()

        dump = RegressorDump(targets, features, dump.X, dump.y, dump.regressor)
        Utils.pickleDump(dump.__dict__, filename)
        self.enmapBox.removeSource(filename)
        self.enmapBox.addSource(filename)

    def onDatasetChanged(self, *args):
        filename = self.mDataset.mFile.filePath()
        try:
            dump = RegressorDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            self.mTargetTable.setRowCount(0)
            return

        # setup targets
        self.mTargetTable.setRowCount(len(dump.targets))
        headers = list()
        for i, target in enumerate(dump.targets):
            colorButton = QgsColorButton(self.mTargetTable)
            colorButton.setColor(QColor(target.color))
            colorButton.setShowMenu(False)
            colorButton.setAutoRaise(True)
            n = dump.y.shape[0]
            self.mTargetTable.setItem(i, 0, QTableWidgetItem(target.name))
            self.mTargetTable.setCellWidget(i, 1, colorButton)
            self.mTargetTable.setCellWidget(i, 2, QLabel(str(n)))

            headers.append(f'Target {i + 1}')
        self.mTargetTable.setVerticalHeaderLabels(headers)

        # setup features
        self.mFeaturesTable.setRowCount(len(dump.features))
        headers = list()
        for i, feature in enumerate(dump.features):
            self.mFeaturesTable.setItem(i, 0, QTableWidgetItem(feature))
            headers.append(f'Feature {i + 1}')
        self.mFeaturesTable.setVerticalHeaderLabels(headers)
        self.mFeaturesTable.resizeColumnsToContents()

    def onRandomSampleClicked(self, *args):
        self.onSaveClicked(question=False)
        filename = self.mDataset.mFile.filePath()
        try:
            dump = RegressorDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            self.mTargetTable.setRowCount(0)
            return

        tmpfile = join(Utils.getTempDirInTempFolder(), basename(filename))
        alg = RandomSamplesFromRegressionDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: filename,
            alg.P_BINS: 1,
            alg.P_OUTPUT_DATASET: tmpfile.replace('.pkl', '.sample.pkl'),
            alg.P_OUTPUT_COMPLEMENT: tmpfile.replace('.pkl', '.complement.pkl'),
        }
        dialog = self.enmapBox.showProcessingAlgorithmDialog(alg, parameters, True, True, None, False, self)
        if len(dialog.results()) == 0:
            return
        filename = dialog.results()[alg.P_OUTPUT_DATASET]
        QMessageBox.information(self, 'Random Sample', f'Open random sample file {basename(filename)}.')
        self.mDataset.mFile.setFilePath(filename)
