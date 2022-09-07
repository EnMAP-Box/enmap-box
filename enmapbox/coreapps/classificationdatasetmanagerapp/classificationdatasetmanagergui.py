from os.path import basename, join

import numpy as np

from enmapboxprocessing.algorithm.randomsamplesfromclassificationdatasetalgorithm import \
    RandomSamplesFromClassificationDatasetAlgorithm
from enmapboxprocessing.parameter.processingparameterpicklefileclassificationdatasetwidget import \
    ProcessingParameterPickleFileClassificationDatasetWidget
from enmapboxprocessing.typing import ClassifierDump, Category
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QLabel, QToolButton, QMessageBox, QComboBox, QSpinBox, QDialog
)
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsColorButton, QgsDoubleSpinBox, QgsSpinBox
from typeguard import typechecked


@typechecked
class ClassificationDatasetManagerGui(QDialog):
    mDataset: ProcessingParameterPickleFileClassificationDatasetWidget
    mCategoryTable: QTableWidget
    mFeaturesTable: QTableWidget
    mRestore: QToolButton
    mSave: QToolButton
    mSampleType: QComboBox
    mSetSampleSize: QToolButton
    mRandomSample: QToolButton
    mRelativeSize: QgsDoubleSpinBox
    mAbsoluteSize: QgsSpinBox

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
        self.mSetSampleSize.clicked.connect(self.onSetSampleSizeClicked)
        self.mRandomSample.clicked.connect(self.onRandomSampleClicked)

    def currentEdits(self):
        filename = self.mDataset.mFile.filePath()
        try:
            dump = ClassifierDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            return

        sizes = list()
        sampleSizes = list()
        categories = list()
        for row in range(self.mCategoryTable.rowCount()):
            value = dump.categories[row].value
            w: QTableWidgetItem = self.mCategoryTable.item(row, 1)
            name = w.text()
            w: QgsColorButton = self.mCategoryTable.cellWidget(row, 2)
            color = w.color().name()
            categories.append(Category(value, name, color))
            w: QLabel = self.mCategoryTable.cellWidget(row, 3)
            size = int(w.text().split(' ')[0])
            sizes.append(size)
            w: QSpinBox = self.mCategoryTable.cellWidget(row, 4)
            sampleSizes.append(w.value())

        features = list()
        for row in range(self.mFeaturesTable.rowCount()):
            w: QTableWidgetItem = self.mFeaturesTable.item(row, 0)
            name = w.text()
            features.append(name)

        return categories, features, sizes, sampleSizes

    def onRestoreClicked(self, *args):
        self.onDatasetChanged()

    def onSaveClicked(self, *args, question=True):
        filename = self.mDataset.mFile.filePath()
        try:
            dump = ClassifierDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            return

        if question:
            button = QMessageBox.question(
                self, 'Save Edits', f'Do you want to save the changes to file {basename(filename)}?'
            )
            if button == QMessageBox.No:
                return

        categories, features, sizes, sampleSizes = self.currentEdits()

        dump = ClassifierDump(categories, features, dump.X, dump.y, dump.classifier)
        Utils.pickleDump(dump.__dict__, filename)
        self.enmapBox.removeSource(filename)
        self.enmapBox.addSource(filename)

    def onDatasetChanged(self, *args):
        filename = self.mDataset.mFile.filePath()
        try:
            dump = ClassifierDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            self.mCategoryTable.setRowCount(0)
            return

        # setup categories
        self.mCategoryTable.setRowCount(len(dump.categories))
        headers = list()
        for i, category in enumerate(dump.categories):
            colorButton = QgsColorButton(self.mCategoryTable)
            colorButton.setColor(QColor(category.color))
            colorButton.setShowMenu(False)
            colorButton.setAutoRaise(True)
            n = int(np.sum(np.equal(dump.y, category.value)))
            self.mCategoryTable.setCellWidget(i, 0, QLabel(str(category.value)))
            self.mCategoryTable.setItem(i, 1, QTableWidgetItem(category.name))
            self.mCategoryTable.setCellWidget(i, 2, colorButton)
            size = f'{n} ({np.round(np.divide(n, len(dump.y)) * 100, 1)}%)'
            self.mCategoryTable.setCellWidget(i, 3, QLabel(size))
            w = QSpinBox()
            w.setMinimum(0)
            w.setMaximum(n)
            w.setValue(0)
            self.mCategoryTable.setCellWidget(i, 4, w)

            headers.append(f'Category {i + 1}')
        self.mCategoryTable.setVerticalHeaderLabels(headers)

        # setup features
        self.mFeaturesTable.setRowCount(len(dump.features))
        headers = list()
        for i, feature in enumerate(dump.features):
            self.mFeaturesTable.setItem(i, 0, QTableWidgetItem(feature))
            headers.append(f'Feature {i + 1}')
        self.mFeaturesTable.setVerticalHeaderLabels(headers)
        self.mFeaturesTable.resizeColumnsToContents()

    def onSetSampleSizeClicked(self, *args):
        categories, features, sizes, sampleSizes = self.currentEdits()

        if self.mSampleType.currentIndex() == self.RelativeSampling:
            p = self.mRelativeSize.value() / 100.
            subsampleSizes = [int(round(n * p)) for n in sizes]
        elif self.mSampleType.currentIndex() == self.AbsoluteSampling:
            subsampleSizes = [self.mAbsoluteSize.value()] * len(categories)
        else:
            raise ValueError()

        for row, n in enumerate(subsampleSizes):
            w: QSpinBox = self.mCategoryTable.cellWidget(row, 4)
            w.setValue(n)

    def onRandomSampleClicked(self, *args):
        self.onSaveClicked(question=False)
        filename = self.mDataset.mFile.filePath()
        try:
            dump = ClassifierDump.fromDict(Utils.pickleLoad(filename))
        except Exception:
            self.mCategoryTable.setRowCount(0)
            return

        categories, features, sizes, sampleSizes = self.currentEdits()

        tmpfile = join(Utils.getTempDirInTempFolder(), basename(filename))
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        parameters = {
            alg.P_DATASET: filename,
            alg.P_N: str(sampleSizes),
            alg.P_OUTPUT_DATASET: tmpfile.replace('.pkl', '.sample.pkl'),
            alg.P_OUTPUT_COMPLEMENT: tmpfile.replace('.pkl', '.complement.pkl'),
        }
        dialog = self.enmapBox.showProcessingAlgorithmDialog(alg, parameters, True, True, None, False, self)
        if len(dialog.results()) == 0:
            return
        filename = dialog.results()[alg.P_OUTPUT_DATASET]
        QMessageBox.information(self, 'Random Sample', f'Open random sample file {basename(filename)}.')
        self.mDataset.mFile.setFilePath(filename)
