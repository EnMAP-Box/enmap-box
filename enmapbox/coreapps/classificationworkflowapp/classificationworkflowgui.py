import traceback
import webbrowser
from functools import wraps, partial
from os.path import join, dirname, exists, basename, isabs, abspath, splitext
from tempfile import gettempdir
from typing import Tuple, Dict, Optional

import numpy as np

from enmapbox import EnMAPBox
from enmapboxprocessing.algorithm.algorithms import algorithms
from enmapboxprocessing.algorithm.classificationperformancesimplealgorithm import \
    ClassificationPerformanceSimpleAlgorithm
from enmapboxprocessing.algorithm.classifierfeaturerankingpermutationimportancealgorithm import \
    ClassifierFeatureRankingPermutationImportanceAlgorithm
from enmapboxprocessing.algorithm.classifierperformancealgorithm import ClassifierPerformanceAlgorithm
from enmapboxprocessing.algorithm.creatergbimagefromclassprobabilityalgorithm import \
    CreateRgbImageFromClassProbabilityAlgorithm
from enmapboxprocessing.algorithm.featureclusteringhierarchicalalgorithm import FeatureClusteringHierarchicalAlgorithm
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.fitgenericclassifieralgorithm import FitGenericClassifierAlgorithm
from enmapboxprocessing.algorithm.fitrandomforestclassifieralgorithm import FitRandomForestClassifierAlgorithm
from enmapboxprocessing.algorithm.predictclassificationalgorithm import PredictClassificationAlgorithm
from enmapboxprocessing.algorithm.predictclassprobabilityalgorithm import PredictClassPropabilityAlgorithm
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
from enmapboxprocessing.algorithm.randomsamplesfromclassificationdatasetalgorithm import \
    RandomSamplesFromClassificationDatasetAlgorithm
from enmapboxprocessing.algorithm.selectfeaturesfromdatasetalgorithm import SelectFeaturesFromDatasetAlgorithm
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
from enmapboxprocessing.parameter.processingparametercodeeditwidget import CodeEditWidget
from enmapboxprocessing.parameter.processingparameterpicklefileclassificationdatasetwidget import \
    ProcessingParameterPickleFileClassificationDatasetWidget
from enmapboxprocessing.parameter.processingparameterpicklefilewidget import ProcessingParameterPickleFileWidget
from enmapboxprocessing.typing import ClassifierDump, Category
from enmapboxprocessing.utils import Utils
from processing.gui.AlgorithmDialog import AlgorithmDialog
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QFont, QColor, QTextCursor
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtWidgets import (
    QMainWindow, QToolButton, QProgressBar, QComboBox, QPlainTextEdit, QCheckBox, QDialog, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QRadioButton, QTextEdit, QWidget
)
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMapLayerProxyModel, Qgis, QgsProcessingFeedback, QgsRasterLayer, QgsProcessing
from qgis.gui import QgsFileWidget, QgsMapLayerComboBox, QgsSpinBox, QgsMessageBar, QgsColorButton, QgsDoubleSpinBox
from typeguard import typechecked


class MissingParameterError(Exception):
    """Methodes decorated with @errorHandled should raise this error to indicate a missing parameter."""


class CancelError(Exception):
    """Methodes decorated with @errorHandled should raise this error to indicate cancelation by the user."""


def errorHandled(func=None, *, successMessage: str = None):
    """Decorator for the various run methods. Will take care of error handling and reporting via the message bar."""
    if func is None:
        return partial(errorHandled, successMessage=successMessage)

    @wraps(func)
    def wrapper(*args, **kwargs):
        gui: ClassificationWorkflowGui
        gui, *argsTail = args
        gui.mMessageBar.clearWidgets()
        try:
            result = func(gui, *argsTail, **kwargs)
        except MissingParameterError as error:
            return
        except CancelError:
            return
        except Exception as error:
            message = traceback.format_exc()
            traceback.print_exc()

            def showError():
                class Dialog(QDialog):
                    def __init__(self):
                        QDialog.__init__(self, gui)
                        self.setWindowTitle('Unexpected error')
                        self.setLayout(QHBoxLayout())
                        widget = QPlainTextEdit(message, parent=self)
                        # widget.setLineWrapMode(QPlainTextEdit.NoWrap)
                        widget.setFont(QFont('Courier'))
                        self.layout().addWidget(widget)

                dialog = Dialog()
                dialog.resize(800, 600)
                dialog.exec_()

            widget = gui.mMessageBar.createMessage('Unexpected error', str(error))
            button = QPushButton(widget)
            button.setText('Traceback')
            button.pressed.connect(showError)
            widget.layout().addWidget(button)
            gui.mMessageBar.pushWidget(widget, Qgis.Critical)
            return

        if successMessage is not None:
            gui.mMessageBar.pushSuccess('Success', successMessage)

        return result

    return wrapper


@typechecked
class ClassificationWorkflowGui(QMainWindow):
    mProgress: QProgressBar
    mCancel: QToolButton
    mLog: QTextEdit
    mLogClear: QToolButton

    # quick mapping
    mQuickDataset: ProcessingParameterPickleFileClassificationDatasetWidget
    mQuickFeatures: QgsMapLayerComboBox
    mQuickComboClassifier: QComboBox
    mQuickCodeClassifier: CodeEditWidget
    mRunQuickMapping: QToolButton
    mQuickCheckPredictedClassification: QCheckBox
    mQuickCheckPredictedProbability: QCheckBox
    mQuickFilePredictedClassification: QgsFileWidget
    mQuickFilePredictedProbability: QgsFileWidget

    # dataset
    # - import
    mAlgoDataset: QComboBox
    mFileDataset: QgsFileWidget
    mViewDataset: QToolButton
    mInfoDataset: QLabel
    mRunImportDataset: QToolButton
    # - preparation
    mRelativeSizeCheck: QRadioButton
    mAbsoluteSizeCheck: QRadioButton
    mRelativeSizeValue: QgsDoubleSpinBox
    mAbsoluteSizeValue: QgsSpinBox
    mSetTrainSize: QToolButton
    mSetTestSize: QToolButton
    mSetSplitSize: QToolButton
    mCategoryTable: QTableWidget
    mFeaturesTable: QTableWidget
    mTableRevert: QToolButton
    mTableSave: QToolButton
    mFileTrainingDataset: QgsFileWidget
    mViewTrainingDataset: QToolButton
    mInfoTrainingDataset: QLabel
    mFileTestDataset: QgsFileWidget
    mViewTestDataset: QToolButton
    mInfoTestDataset: QLabel
    mRunSplitDataset: QToolButton

    # classifier
    mComboClassifier: QComboBox
    mCodeClassifier: CodeEditWidget

    # feature selection
    # - clustering
    #   - analysis
    mDataClustering: QComboBox
    mAlgoClustering: QComboBox
    mFileClusteringReport: QgsFileWidget
    mViewClusteringReport: QToolButton
    mRunClustering: QToolButton
    #   - subset selection
    mNClustering: QgsSpinBox
    mFileTrainingDatasetClustered: QgsFileWidget
    mViewTrainingDatasetClustered: QToolButton
    mInfoTrainingDatasetClustered: QLabel
    mFileTestDatasetClustered: QgsFileWidget
    mViewTestDatasetClustered: QToolButton
    mInfoTestDatasetClustered: QLabel
    mRunClusteringSelect: QToolButton
    # - ranking
    #   - analysis
    mDataRanking: QComboBox
    mAlgoRanking: QComboBox
    mFileRankingReport: QgsFileWidget
    mViewRankingReport: QToolButton
    mRunRanking: QToolButton
    #   - subset selection
    mNRanking: QgsSpinBox
    mFileTrainingDatasetRanked: QgsFileWidget
    mViewTrainingDatasetRanked: QToolButton
    mInfoTrainingDatasetRanked: QLabel
    mFileTestDatasetRanked: QgsFileWidget
    mViewTestDatasetRanked: QToolButton
    mInfoTestDatasetRanked: QLabel
    mRunRankingSelect: QToolButton

    # model
    # - fit
    mDataFit: QComboBox
    mFileClassifierFitted: QgsFileWidget
    mViewClassifierFitted: QToolButton
    mRunClassifierFit: QToolButton
    # - performance
    mAlgoClassifierPerformance: QComboBox
    mFileClassifierPerformanceReport: QgsFileWidget
    mViewClassifierPerformanceReport: QToolButton
    mRunClassifierPerformance: QToolButton

    # classification
    # - predict
    mPredictClassifier: ProcessingParameterPickleFileWidget
    mPredictFeatures: QgsMapLayerComboBox
    mCheckPredictedClassification: QCheckBox
    mCheckPredictedProbability: QCheckBox
    mFilePredictedClassification: QgsFileWidget
    mFilePredictedProbability: QgsFileWidget
    mRunPredict: QToolButton
    # - performance
    mPredictedClassification: QgsMapLayerComboBox
    mObservedClassification: QgsMapLayerComboBox
    mFileClassificationPerformanceReport: QgsFileWidget
    mViewClassificationPerformanceReport: QToolButton
    mRunClassificationPerformance: QToolButton

    # settings
    mWorkingDirectory: QgsFileWidget
    mOpenWorkingDirectory: QToolButton
    mDialogAutoClose: QCheckBox
    mDialogAutoRun: QCheckBox
    mDialogAutoOpen: QCheckBox

    # help
    mWebView: QWebView
    mWebHome: QToolButton
    mWebBack: QToolButton
    mWebForward: QToolButton
    mWebReadTheDocs: QToolButton

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi(join(dirname(__file__), 'main.ui'), self)
        self.url = QUrl(
            'https://enmap-box.readthedocs.io/en/latest/usr_section/usr_manual/applications.html#classification-workflow')
        self.mMessageBar = QgsMessageBar()
        self.mMessageBar.setMaximumSize(9999999, 50)
        self.centralWidget().layout().addWidget(self.mMessageBar)
        self.connectSignals()
        self.initFiles()
        self.initLayers()
        self.initClassifier()
        self.enmapBox = EnMAPBox.instance()

    def connectSignals(self):
        self.mLogClear.clicked.connect(lambda: self.mLog.clear())

        # quick mapping
        self.mQuickComboClassifier.currentIndexChanged.connect(self.onClassifierChanged)
        self.mRunQuickMapping.clicked.connect(self.runQuickMapping)

        # dataset
        # - creation
        self.mFileDataset.fileChanged.connect(self.onDatasetChanged)
        self.mViewDataset.clicked.connect(self.onViewFile)
        self.mRunImportDataset.clicked.connect(self.runImportDataset)
        # - style and split
        self.mSetTrainSize.clicked.connect(self.onSetTrainSize)
        self.mSetTestSize.clicked.connect(self.onSetTestSize)
        self.mSetSplitSize.clicked.connect(self.onSetSplitSize)
        self.mTableRevert.clicked.connect(self.onDatasetChanged)  # just reload the sample
        self.mTableSave.clicked.connect(self.onDatasetTableSave)
        self.mViewTrainingDataset.clicked.connect(self.onViewFile)
        self.mViewTestDataset.clicked.connect(self.onViewFile)
        self.mRunSplitDataset.clicked.connect(self.runSplitDataset)

        # classifier
        self.mComboClassifier.currentIndexChanged.connect(self.onClassifierChanged)

        # feature selection
        # - clustering
        #   - analysis
        self.mViewClusteringReport.clicked.connect(self.onViewFile)
        self.mRunClustering.clicked.connect(self.runFeatureClustering)
        #   - subset selection
        self.mViewTrainingDatasetClustered.clicked.connect(self.onViewFile)
        self.mViewTestDatasetClustered.clicked.connect(self.onViewFile)
        self.mRunClusteringSelect.clicked.connect(self.runFeatureClusteringSelect)

        # - ranking
        #   - analysis
        self.mViewRankingReport.clicked.connect(self.onViewFile)
        self.mRunRanking.clicked.connect(self.runFeatureRanking)
        #   - subset selection
        self.mViewTrainingDatasetRanked.clicked.connect(self.onViewFile)
        self.mViewTestDatasetRanked.clicked.connect(self.onViewFile)
        self.mRunRankingSelect.clicked.connect(self.runFeatureRankingSelect)

        # model
        # - fit
        self.mViewClassifierFitted.clicked.connect(self.onViewFile)
        self.mRunClassifierFit.clicked.connect(self.runClassifierFit)
        # - performance
        self.mViewClassifierPerformanceReport.clicked.connect(self.onViewFile)
        self.mRunClassifierPerformance.clicked.connect(self.runClassifierPerformance)

        # classification
        # - predict
        self.mRunPredict.clicked.connect(self.runPredict)
        # - performance
        self.mRunClassificationPerformance.clicked.connect(self.runClassificationPerformance)
        self.mViewClassificationPerformanceReport.clicked.connect(self.onViewFile)

        # help
        self.mWebHome.clicked.connect(lambda: self.mWebView.setUrl(self.url))
        self.mWebBack.clicked.connect(self.mWebView.back)
        self.mWebForward.clicked.connect(self.mWebView.forward)
        self.mWebReadTheDocs.clicked.connect(lambda: webbrowser.open_new_tab(self.url.toString()))

        # update dataset description labels
        self.mFileDataset.fileChanged.connect(
            lambda: self.updateDatasetInfo(self.mFileDataset, self.mInfoDataset)
        )
        self.mFileTrainingDataset.fileChanged.connect(
            lambda: self.updateDatasetInfo(self.mFileTrainingDataset, self.mInfoTrainingDataset)
        )
        self.mFileTrainingDatasetClustered.fileChanged.connect(
            lambda: self.updateDatasetInfo(self.mFileTrainingDatasetClustered, self.mInfoTrainingDatasetClustered)
        )
        self.mFileTrainingDatasetRanked.fileChanged.connect(
            lambda: self.updateDatasetInfo(self.mFileTrainingDatasetRanked, self.mInfoTrainingDatasetRanked)
        )
        self.mFileTestDataset.fileChanged.connect(
            lambda: self.updateDatasetInfo(self.mFileTestDataset, self.mInfoTestDataset)
        )
        self.mFileTestDatasetClustered.fileChanged.connect(
            lambda: self.updateDatasetInfo(self.mFileTestDatasetClustered, self.mInfoTestDatasetClustered)
        )
        self.mFileTestDatasetRanked.fileChanged.connect(
            lambda: self.updateDatasetInfo(self.mFileTestDatasetRanked, self.mInfoTestDatasetRanked)
        )
        for label in [self.mInfoDataset,
                      self.mInfoTrainingDataset, self.mInfoTrainingDatasetClustered, self.mInfoTrainingDatasetRanked,
                      self.mInfoTestDataset, self.mInfoTestDatasetClustered, self.mInfoTestDatasetRanked]:
            label.hide()

        # update default roots when working directory changed
        self.mWorkingDirectory.fileChanged.connect(self.onWorkingDirectoryChanged)
        self.mOpenWorkingDirectory.clicked.connect(lambda: webbrowser.open_new(self.mWorkingDirectory.filePath()))

    def initFiles(self):
        self.mWebView.setUrl(self.url)
        self.mWebHome.clicked.emit()
        self.mWorkingDirectory.setFilePath(join(gettempdir(), 'EnMAPBox', 'ClassificationWorkflow'))
        self.onWorkingDirectoryChanged()
        self.defaultBasenames = {
            self.mFileDataset.objectName(): 'dataset.pkl',
            self.mFileTrainingDataset.objectName(): 'training_dataset.pkl',
            self.mFileTestDataset.objectName(): 'test_dataset.pkl',
            self.mFileTrainingDatasetClustered.objectName(): 'training_dataset_clustered.pkl',
            self.mFileTestDatasetClustered.objectName(): 'test_dataset_clustered.pkl',
            self.mFileTrainingDatasetRanked.objectName(): 'training_dataset_ranked.pkl',
            self.mFileTestDatasetRanked.objectName(): 'test_dataset_ranked.pkl',
            self.mFileClassifierFitted.objectName(): 'classifier_fitted.pkl',
            self.mFileClusteringReport.objectName(): 'clustering_report.html',
            self.mFileRankingReport.objectName(): 'ranking_report.html',
            self.mFileClassifierPerformanceReport.objectName(): 'classifier_performance_report.html',
            self.mFilePredictedClassification.objectName(): 'classification.tif',
            self.mFilePredictedProbability.objectName(): 'probability.tif',
            self.mFileClassificationPerformanceReport.objectName(): 'classification_performance_report.html',
        }

        for objectName, name in self.defaultBasenames.items():
            getattr(self, objectName).setFilePath(name)

    def initLayers(self):
        self.mPredictFeatures.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mQuickFeatures.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mPredictedClassification.setFilters(QgsMapLayerProxyModel.RasterLayer)

    def initClassifier(self):
        self.classifierNames = list()
        self.classifierCodes = list()
        alg: FitClassifierAlgorithmBase
        i = 0
        for alg in algorithms():
            if not isinstance(alg, FitClassifierAlgorithmBase):
                continue
            if isinstance(alg, FitGenericClassifierAlgorithm):
                continue
            if isinstance(alg, FitRandomForestClassifierAlgorithm):
                index = i
            i += 1
            self.classifierNames.append(alg.displayName().replace('Fit ', ''))
            self.classifierCodes.append(alg.defaultCodeAsString())
        self.mQuickComboClassifier.addItems(self.classifierNames)
        self.mComboClassifier.addItems(self.classifierNames)
        self.mCodeClassifier.setText(FitRandomForestClassifierAlgorithm().defaultCodeAsString())
        self.mQuickCodeClassifier.setText(FitRandomForestClassifierAlgorithm().defaultCodeAsString())
        self.mQuickComboClassifier.setCurrentIndex(index)
        self.mComboClassifier.setCurrentIndex(index)

    def _createAlgorithmDialogWrapper(self):
        class AlgorithmDialogWrapper(AlgorithmDialog):
            def __init__(self_, *args, **kwargs):
                AlgorithmDialog.__init__(self_, *args, **kwargs)
                self_.finishedSuccessful = False
                self_.finishResult = None

            def finish(self_, successful, result, context, feedback, in_place=False):
                super().finish(successful, result, context, feedback, in_place)
                self_.finishedSuccessful = successful
                self_.finishResult = result
                if successful:
                    if self.mDialogAutoClose.isChecked():
                        self_.close()
                        feedback: QgsProcessingFeedback = self_.feedback
                        self.mLog.moveCursor(QTextCursor.End)
                        self.mLog.insertPlainText(feedback.textLog() + '\n##########\n\n')
                        self.mLog.verticalScrollBar().setValue(self.mLog.verticalScrollBar().maximum())

        return AlgorithmDialogWrapper

    def showAlgorithmDialog(self, alg: EnMAPProcessingAlgorithm, parameters: Dict = None, autoRun: bool = None) -> Dict:
        if autoRun is None:
            autoRun = self.mDialogAutoRun.isChecked()
        wrapper = self._createAlgorithmDialogWrapper()
        dialog = self.enmapBox.showProcessingAlgorithmDialog(
            alg, parameters=parameters, show=True, modal=True, parent=self, wrapper=wrapper, autoRun=autoRun
        )

        if dialog.finishedSuccessful:
            if self.mDialogAutoOpen.isChecked():
                for value in dialog.finishResult.values():
                    if isinstance(value, str) and value.endswith('.html'):
                        self.openWebbrowser(value)
            return dialog.finishResult
        else:
            raise CancelError()

    @errorHandled(successMessage='performed quick mapping')
    def runQuickMapping(self, *args):

        # check consistency
        if self.mQuickDataset.value() == '':
            self.pushParameterMissing('Classification dataset for training', 'select a dataset first')
            raise MissingParameterError()
        if self.mQuickFeatures.currentLayer() is None:
            self.pushParameterMissing('Raster layer for mapping', 'select a raster first')
            raise MissingParameterError()

        # set dataset
        self.mFileDataset.setFilePath(self.mQuickDataset.value())

        # fit classifier
        self.mFileClassifierFitted.setFilePath('')
        self.mDataFit.setCurrentIndex(1)  # (original) dataset
        self.mRunClassifierFit.clicked.emit()
        if self.mFileClassifierFitted.filePath() == '':  # if fitting was canceled return silently
            return

        # mapping
        self.mPredictFeatures.setLayer(self.mQuickFeatures.currentLayer())
        self.mCheckPredictedClassification.setChecked(self.mQuickCheckPredictedClassification.isChecked())
        self.mCheckPredictedProbability.setChecked(self.mQuickCheckPredictedProbability.isChecked())
        self.mFilePredictedProbability.setFilePath(self.mQuickFilePredictedProbability.filePath())
        self.mFilePredictedClassification.setFilePath(self.mQuickFilePredictedClassification.filePath())
        self.mRunPredict.clicked.emit()
        self.mQuickFilePredictedProbability.setFilePath(self.mFilePredictedProbability.filePath())
        self.mQuickFilePredictedClassification.setFilePath(self.mFilePredictedClassification.filePath())

    @errorHandled(successMessage='created dataset')
    def runImportDataset(self, *args, parameters=None, autoRun=False):

        if self.mAlgoDataset.currentIndex() < 1:
            self.pushParameterMissing('Source', 'select source first')
            raise MissingParameterError()

        Algs = [None,
                PrepareClassificationDatasetFromCategorizedRasterAlgorithm,
                PrepareClassificationDatasetFromCategorizedVectorAlgorithm,
                PrepareClassificationDatasetFromCategorizedVectorAndFieldsAlgorithm,
                PrepareClassificationDatasetFromCategorizedLibraryAlgorithm,
                PrepareClassificationDatasetFromTableAlgorithm,
                PrepareClassificationDatasetFromFilesAlgorithm,
                PrepareClassificationDatasetFromCodeAlgorithm]
        Alg = Algs[self.mAlgoDataset.currentIndex()]
        alg = Alg()

        if parameters is None:
            parameters = dict()
        parameters[alg.P_OUTPUT_DATASET] = self.createOutputFilename(self.mFileDataset, '.pkl')
        result = self.showAlgorithmDialog(alg, parameters, autoRun=autoRun)
        self.mFileDataset.setFilePath(result[alg.P_OUTPUT_DATASET])

    def getDataset(self) -> str:
        filename = self.createInputFilename(self.mFileDataset)
        if filename is None:
            self.pushParameterMissing(self.tabPath(self.mFileDataset), '', self.mRunImportDataset.text())
            raise MissingParameterError()
        return filename

    def getTrainingDataset(self) -> str:
        filename = self.createInputFilename(self.mFileTrainingDataset)
        if filename is None:
            self.pushParameterMissing(self.tabPath(self.mFileTrainingDataset), '', self.mRunSplitDataset.text())
            raise MissingParameterError()
        return filename

    def getTrainingDatasetClustered(self) -> str:
        filename = self.createInputFilename(self.mFileTrainingDatasetClustered)
        if filename is None:
            self.pushParameterMissing(
                self.tabPath(self.mFileTrainingDatasetClustered), '', self.mRunClusteringSelect.text()
            )
            raise MissingParameterError()
        return filename

    def getTrainingDatasetRanked(self) -> str:
        filename = self.createInputFilename(self.mFileTrainingDatasetRanked)
        if filename is None:
            self.pushParameterMissing(
                self.tabPath(self.mFileTrainingDatasetRanked), '', self.mRunRankingSelect.text()
            )
            raise MissingParameterError()
        return filename

    def getTestDataset(self, allowEmpty=True) -> Optional[str]:
        filename = self.createInputFilename(self.mFileTestDataset)
        if filename is None and not allowEmpty:
            self.pushParameterMissing(self.tabPath(self.mFileTestDataset), '', self.mRunSplitDataset.text())
            raise MissingParameterError()
        return filename

    def getTestDatasetClustered(self, allowEmpty=True) -> Optional[str]:
        filename = self.createInputFilename(self.mFileTestDatasetClustered)
        if filename is None and not allowEmpty:
            self.pushParameterMissing(
                self.tabPath(self.mFileTestDatasetClustered), '', self.mRunClusteringSelect.text()
            )
            raise MissingParameterError()
        return filename

    def getTestDatasetRanked(self, allowEmpty=True) -> Optional[str]:
        filename = self.createInputFilename(self.mFileTestDatasetRanked)
        if filename is None and not allowEmpty:
            self.pushParameterMissing(
                self.tabPath(self.mFileTestDatasetRanked), '', self.mRunRankingSelect.text()
            )
            raise MissingParameterError()
        return filename

    def getTrainingDatasetByIndex(self, index) -> str:
        if index == 1:
            return self.getDataset()
        if index == 2:
            return self.getTrainingDataset()
        if index == 3:
            return self.getTrainingDatasetClustered()
        if index == 4:
            return self.getTrainingDatasetRanked()
        self.pushParameterMissing('Dataset', 'select dataset first')
        raise MissingParameterError()

    def getTestDatasetByIndex(self, index, allowEmpty=True) -> Optional[str]:
        if index == 1:
            if allowEmpty:
                return self.createInputFilename(self.mFileDataset)
            else:
                return self.getDataset()
        if index == 2:
            return self.getTestDataset(allowEmpty)
        if index == 3:
            return self.getTestDatasetClustered(allowEmpty)
        if index == 4:
            return self.getTestDatasetRanked(allowEmpty)
        self.pushParameterMissing('Dataset', 'select dataset first')
        raise MissingParameterError()

    def getClusteringReport(self) -> str:
        filename = self.createInputFilename(self.mFileClusteringReport)
        if filename is None:
            self.pushParameterMissing(
                self.tabPath(self.mFileClusteringReport), '', self.mRunClustering.text()
            )
            raise MissingParameterError()
        return filename

    def getRankingReport(self) -> str:
        filename = self.createInputFilename(self.mFileRankingReport)
        if filename is None:
            self.pushParameterMissing(
                self.tabPath(self.mFileRankingReport), '', self.mRunRanking.text()
            )
            raise MissingParameterError()
        return filename

    def getClusteringN(self) -> int:
        n = self.mNClustering.value()
        if n == 0:
            self.pushParameterWrongValue('Number of features', 'select value greater 0')
            raise MissingParameterError()
        return n

    def getRankingN(self) -> int:
        n = self.mNRanking.value()
        if n == 0:
            self.pushParameterWrongValue('Number of features', 'select value greater 0')
            raise MissingParameterError()
        return n

    def getClassifier(self) -> str:
        import processing
        alg = FitGenericClassifierAlgorithm()
        parameters = {alg.P_CLASSIFIER: self.mCodeClassifier.text(),
                      alg.P_OUTPUT_CLASSIFIER: join(Utils.getTempDirInTempFolder(), 'classifier.pkl')}
        result = processing.run(alg, parameters)
        filename = result[alg.P_OUTPUT_CLASSIFIER]
        return filename

    def getClassifierFitted(self) -> str:
        filename = self.mPredictClassifier.filePath()
        if filename is None:
            self.pushParameterMissing(
                self.tabPath(self.mFileClassifierFitted), '', self.mRunClassifierFit.text()
            )
            raise MissingParameterError()
        return filename

    def getPredictedClassification(self, allowEmpty=False) -> str:
        filename = self.createInputFilename(self.mFilePredictedClassification)
        if allowEmpty:
            return filename
        if filename is None:
            self.pushParameterMissing(
                self.tabPath(self.mFilePredictedClassification), '', self.mRunPredict.text()
            )
            raise MissingParameterError()
        return filename

    @errorHandled(successMessage='split sample')
    def runSplitDataset(self, *args):
        filename = self.getDataset()
        trainNs = list()
        testNs = list()
        for i in range(self.mCategoryTable.rowCount()):
            trainN: QgsSpinBox = self.mCategoryTable.cellWidget(i, 4)
            testN: QgsSpinBox = self.mCategoryTable.cellWidget(i, 5)
            trainNs.append(trainN.value())
            testNs.append(testN.value())

        # draw train sample
        alg = RandomSamplesFromClassificationDatasetAlgorithm()
        parameters = {alg.P_DATASET: filename,
                      alg.P_N: str(trainNs),
                      alg.P_OUTPUT_DATASET: self.createOutputFilename(self.mFileTrainingDataset, '.pkl'),
                      alg.P_OUTPUT_COMPLEMENT: QgsProcessing.TEMPORARY_OUTPUT,
                      }
        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileTrainingDataset.setFilePath(result[alg.P_OUTPUT_DATASET])
        filenameComplement = result[alg.P_OUTPUT_COMPLEMENT]

        # draw test sample from complement
        if sum(testNs) == 0:
            self.mFileTestDataset.setFilePath('')
        else:
            parameters = {alg.P_DATASET: filenameComplement,
                          alg.P_N: str(testNs),
                          alg.P_OUTPUT_DATASET: self.createOutputFilename(self.mFileTestDataset, '.pkl')}
            result = self.showAlgorithmDialog(alg, parameters)
            self.mFileTestDataset.setFilePath(result[alg.P_OUTPUT_DATASET])

        if sum(trainNs) == 0:
            self.mFileTrainingDataset.setFilePath('')

    @errorHandled(successMessage='clustered features')
    def runFeatureClustering(self, *args):

        filenameTrain = self.getTrainingDatasetByIndex(self.mDataClustering.currentIndex())

        if self.mAlgoClustering.currentIndex() > 0:
            Alg = [None, FeatureClusteringHierarchicalAlgorithm][self.mAlgoClustering.currentIndex()]
            alg = Alg()
        else:
            self.pushParameterMissing('Algorithm', 'select algorithm first')
            raise MissingParameterError()

        parameters = {alg.P_DATASET: filenameTrain,
                      alg.P_OUTPUT_REPORT: self.createOutputFilename(self.mFileClusteringReport, '.html')}
        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileClusteringReport.setFilePath(result[alg.P_OUTPUT_REPORT])

    @errorHandled(successMessage='selected most representative features')
    def runFeatureClusteringSelect(self, *args):

        filenameTrain = self.getTrainingDatasetByIndex(self.mDataClustering.currentIndex())
        filenameTest = self.getTestDatasetByIndex(self.mDataClustering.currentIndex())
        filenameClustering = self.getClusteringReport()
        n = self.getClusteringN()
        # get feature subset
        dump = Utils.jsonLoad(filenameClustering + '.json')
        featureList = [index + 1 for index in dump['feature_subset_hierarchy'][n - 1]]

        # subset train sample
        alg = SelectFeaturesFromDatasetAlgorithm()
        parameters = {alg.P_DATASET: filenameTrain,
                      alg.P_FEATURE_LIST: str(featureList),
                      alg.P_OUTPUT_DATASET: self.createOutputFilename(self.mFileTrainingDatasetClustered, '.pkl')}
        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileTrainingDatasetClustered.setFilePath(result[alg.P_OUTPUT_DATASET])

        # subset test sample
        if filenameTest is not None:
            alg = SelectFeaturesFromDatasetAlgorithm()
            parameters = {alg.P_DATASET: filenameTest,
                          alg.P_FEATURE_LIST: str(featureList),
                          alg.P_OUTPUT_DATASET: self.createOutputFilename(self.mFileTestDatasetClustered, '.pkl')}
            result = self.showAlgorithmDialog(alg, parameters)
            self.mFileTestDatasetClustered.setFilePath(result[alg.P_OUTPUT_DATASET])

    @errorHandled(successMessage='ranked features')
    def runFeatureRanking(self, *args):

        filenameTrain = self.getTrainingDatasetByIndex(self.mDataRanking.currentIndex())
        filenameTest = self.getTestDatasetByIndex(self.mDataRanking.currentIndex())
        filenameClassifier = self.getClassifier()

        if self.mAlgoRanking.currentIndex() > 0:
            Alg = [
                None,
                None,
                ClassifierFeatureRankingPermutationImportanceAlgorithm,
                None,
                None,
                None
            ][self.mAlgoRanking.currentIndex()]
            if Alg is None:
                raise NotImplementedError()  # todo implement all algos!
            alg = Alg()
        else:
            self.pushParameterMissing('Algorithm', 'select algorithm first')
            raise MissingParameterError()

        parameters = {alg.P_TRAIN_DATASET: filenameTrain,
                      alg.P_TEST_DATASET: filenameTest,
                      alg.P_CLASSIFIER: filenameClassifier,
                      alg.P_REPEATS: 10,
                      alg.P_OUTPUT_REPORT: self.createOutputFilename(self.mFileRankingReport, '.html')}
        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileRankingReport.setFilePath(result[alg.P_OUTPUT_REPORT])

    @errorHandled(successMessage='selected most important features')
    def runFeatureRankingSelect(self, *args):
        filenameTrain = self.getTrainingDatasetByIndex(self.mDataRanking.currentIndex())
        filenameTest = self.getTestDatasetByIndex(self.mDataRanking.currentIndex())
        filenameRanking = self.getRankingReport()
        n = self.getRankingN()

        # get feature subset
        dump = Utils.jsonLoad(filenameRanking + '.json')
        featureList = [index + 1 for index in dump['feature_subset_hierarchy'][n - 1]]

        # subset train sample
        alg = SelectFeaturesFromDatasetAlgorithm()
        parameters = {alg.P_DATASET: filenameTrain,
                      alg.P_FEATURE_LIST: str(featureList),
                      alg.P_OUTPUT_DATASET: self.createOutputFilename(self.mFileTrainingDatasetRanked, '.pkl')}
        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileTrainingDatasetRanked.setFilePath(result[alg.P_OUTPUT_DATASET])

        # subset test sample
        if filenameTest is not None:
            alg = SelectFeaturesFromDatasetAlgorithm()
            parameters = {alg.P_DATASET: filenameTest,
                          alg.P_FEATURE_LIST: str(featureList),
                          alg.P_OUTPUT_DATASET: self.createOutputFilename(self.mFileTestDatasetRanked, '.pkl')}
            result = self.showAlgorithmDialog(alg, parameters)
            self.mFileTestDatasetRanked.setFilePath(result[alg.P_OUTPUT_DATASET])

    @errorHandled(successMessage='fitted classifier')
    def runClassifierFit(self, *args):
        filenameTrain = self.getTrainingDatasetByIndex(self.mDataFit.currentIndex())

        alg = FitGenericClassifierAlgorithm()
        parameters = {alg.P_DATASET: filenameTrain,
                      alg.P_CLASSIFIER: self.mCodeClassifier.text(),
                      alg.P_OUTPUT_CLASSIFIER: self.createOutputFilename(self.mFileClassifierFitted, '.pkl')
                      }
        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileClassifierFitted.setFilePath(result[alg.P_OUTPUT_CLASSIFIER])
        self.mPredictClassifier.setFilePath(result[alg.P_OUTPUT_CLASSIFIER])

    @errorHandled(successMessage='assessed classifier performance')
    def runClassifierPerformance(self, *args):
        filenameTrain = self.getTrainingDatasetByIndex(self.mDataFit.currentIndex())

        alg = ClassifierPerformanceAlgorithm()
        parameters = {alg.P_OUTPUT_REPORT: self.createOutputFilename(self.mFileClassifierPerformanceReport, '.html')}

        if self.mAlgoClassifierPerformance.currentIndex() == 0:
            self.pushParameterMissing('Algorithm', 'select algorithm first')
            raise MissingParameterError()

        if self.mAlgoClassifierPerformance.currentIndex() == 1:  # cross-validation performance
            parameters[alg.P_CLASSIFIER] = self.getClassifier()
            parameters[alg.P_DATASET] = filenameTrain
            parameters[alg.P_NFOLD] = 10

        if self.mAlgoClassifierPerformance.currentIndex() == 2:  # test dataset performance
            filenameTest = self.getTestDatasetByIndex(self.mDataFit.currentIndex(), allowEmpty=False)
            parameters[alg.P_CLASSIFIER] = self.getClassifierFitted()
            parameters[alg.P_DATASET] = filenameTest

        if self.mAlgoClassifierPerformance.currentIndex() == 3:  # training dataset performance
            parameters[alg.P_CLASSIFIER] = self.getClassifierFitted()
            parameters[alg.P_DATASET] = filenameTrain

        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileClassifierPerformanceReport.setFilePath(result[alg.P_OUTPUT_REPORT])

    @errorHandled(successMessage='predicted maps')
    def runPredict(self, *args):

        filenameClassifier = self.getClassifierFitted()
        raster: QgsRasterLayer = self.mPredictFeatures.currentLayer()
        if raster is None:
            self.pushParameterMissingLayer('Raster layer with features')
            raise MissingParameterError()

        if self.mCheckPredictedClassification.isChecked():
            # classification
            filenameClassification = self.createOutputFilename(self.mFilePredictedClassification, '.tif')
            alg = PredictClassificationAlgorithm()
            parameters = {
                alg.P_CLASSIFIER: filenameClassifier,
                alg.P_RASTER: raster,
                alg.P_OUTPUT_CLASSIFICATION: filenameClassification
            }
            result = self.showAlgorithmDialog(alg, parameters)
            self.mFilePredictedClassification.setFilePath(filenameClassification)

        if self.mCheckPredictedProbability.isChecked():
            # probability
            filenameProbability = self.createOutputFilename(self.mFilePredictedProbability, '.tif')
            filenameRgb = self.createOutputFilename(self.mFilePredictedProbability, '.tif', suffix='_rgb')
            alg = PredictClassPropabilityAlgorithm()
            parameters = {
                alg.P_CLASSIFIER: filenameClassifier,
                alg.P_RASTER: raster,
                alg.P_OUTPUT_PROBABILITY: filenameProbability
            }
            result = self.showAlgorithmDialog(alg, parameters)
            self.mFilePredictedProbability.setFilePath(filenameProbability)

            # probability as RGB
            colors = str([c.color for c in ClassifierDump(**Utils.pickleLoad(filenameClassifier)).categories])
            alg = CreateRgbImageFromClassProbabilityAlgorithm()
            parameters = {
                alg.P_PROBABILITY: filenameProbability,
                alg.P_COLORS: colors,
                alg.P_OUTPUT_RGB: filenameRgb
            }
            result = self.showAlgorithmDialog(alg, parameters)

    @errorHandled(successMessage='predicted maps')
    def runClassificationPerformance(self, *args):
        predicted = self.getPredictedClassification()
        observed: QgsRasterLayer = self.mObservedClassification.currentLayer()
        if observed is None:
            self.pushParameterMissingLayer('Observed categorized layer')
            raise MissingParameterError()

        alg = ClassificationPerformanceSimpleAlgorithm()
        parameters = {alg.P_CLASSIFICATION: predicted,
                      alg.P_REFERENCE: observed,
                      alg.P_OUTPUT_REPORT: self.createOutputFilename(self.mFileClassificationPerformanceReport,
                                                                     '.html')}
        result = self.showAlgorithmDialog(alg, parameters)
        self.mFileClassificationPerformanceReport.setFilePath(result[alg.P_OUTPUT_REPORT])

    def createOutputFilename(self, mFile: QgsFileWidget, extension: str, suffix='') -> str:

        defaultBasename = splitext(self.defaultBasenames[mFile.objectName()])[0]

        if mFile.filePath() == '':
            filename = join(self.mWorkingDirectory.filePath(), defaultBasename + suffix + extension)
        else:
            filename = mFile.filePath()

        if not isabs(filename):
            filename = abspath(join(self.mWorkingDirectory.filePath(), filename))

        if not filename.endswith(extension):
            filename += extension

        if not exists(filename):
            return filename

        if not basename(filename).startswith(defaultBasename):
            return filename

        # give it a unique number
        i = 2
        while True:
            filename = join(dirname(filename), defaultBasename + suffix + f'_{i}' + extension)
            if not exists(filename):
                break
            i += 1

        return filename

    def createInputFilename(self, mFile: QgsFileWidget) -> Optional[str]:
        filename = mFile.filePath()
        if not exists(filename):
            return None
        return filename

    def updateDatasetInfo(self, mFile: QgsFileWidget, label: QLabel):
        filename = mFile.filePath()
        if exists(filename) and filename.endswith('.pkl'):
            dump = ClassifierDump(**Utils.pickleLoad(filename))
            label.setText(f'{np.array(dump.X).shape[0]} '
                          f'samples {np.array(dump.X).shape[1]} features  {len(dump.categories)} categories')
            label.show()
        else:
            label.setText('')
            label.hide()

    @errorHandled
    def onClassifierChanged(self, index: int):
        self.mComboClassifier.setCurrentIndex(index)
        self.mQuickComboClassifier.setCurrentIndex(index)
        text = self.classifierCodes[index]
        self.mCodeClassifier.setText(text)
        self.mQuickCodeClassifier.setText(text)

    @errorHandled
    def onWorkingDirectoryChanged(self, *args):
        wd = self.mWorkingDirectory.filePath()
        for mFile in [self.mFileDataset, self.mFileTrainingDataset, self.mFileTestDataset,
                      self.mFileTrainingDatasetClustered, self.mFileTestDatasetClustered,
                      self.mFileTrainingDatasetRanked, self.mFileTestDatasetRanked,
                      self.mFileClassifierFitted,
                      self.mFileClusteringReport, self.mFileRankingReport,
                      self.mFileClassifierPerformanceReport, self.mFileClassificationPerformanceReport]:
            mFile.setDefaultRoot(wd)

    @errorHandled
    def onDatasetChanged(self, *args):
        filename = self.mFileDataset.filePath()
        if exists(filename) and filename.endswith('.pkl'):
            dump = ClassifierDump(**Utils.pickleLoad(filename))
        else:
            dump = ClassifierDump(categories=[], features=[], X=np.zeros((0, 0)), y=np.zeros((0, 1)))

        self.updateDatasetInfo(self.mFileDataset, self.mInfoDataset)

        def makeSpinBoxes(c: Category) -> Tuple[int, QgsSpinBox, QgsSpinBox]:
            n = int(np.sum(np.equal(dump.y, c.value)))
            trainN = QgsSpinBox(self.mCategoryTable)
            testN = QgsSpinBox(self.mCategoryTable)
            trainN.setMinimum(0)
            trainN.setMaximum(n)
            trainN.setValue(n)
            testN.setMinimum(0)
            testN.setMaximum(n)
            testN.setValue(0)
            trainN.valueChanged.connect(lambda v: testN.setValue(min(testN.value(), n - v)))
            testN.valueChanged.connect(lambda v: trainN.setValue(min(trainN.value(), n - v)))
            return n, trainN, testN

        # setup categories
        self.mCategoryTable.setRowCount(len(dump.categories))
        headers = list()
        for i, category in enumerate(dump.categories):
            colorButton = QgsColorButton(self.mCategoryTable)
            colorButton.setColor(QColor(category.color))
            colorButton.setShowMenu(False)
            colorButton.setAutoRaise(True)
            n, trainN, testN = makeSpinBoxes(category)
            self.mCategoryTable.setCellWidget(i, 0, QLabel(f'  {category.value}  ', self.mCategoryTable))
            self.mCategoryTable.setItem(i, 1, QTableWidgetItem(category.name))
            self.mCategoryTable.setCellWidget(i, 2, colorButton)
            if len(dump.y) > 0:
                size = f'  {n} / {np.round(np.divide(n, len(dump.y)) * 100, 1)}%  '
            else:
                size = f'  {n}  '
            self.mCategoryTable.setCellWidget(i, 3, QLabel(size, self.mCategoryTable))
            self.mCategoryTable.setCellWidget(i, 4, trainN)
            self.mCategoryTable.setCellWidget(i, 5, testN)
            # headers.append(f'{category.value}: {category.name} [{n}] ({round(n / len(dump.y) * 100, 1)}%)')
            headers.append(f'Category {i + 1}')
        self.mCategoryTable.setVerticalHeaderLabels(headers)
        self.mCategoryTable.resizeColumnsToContents()

        # setup features
        self.mFeaturesTable.setRowCount(len(dump.features))
        headers = list()
        for i, feature in enumerate(dump.features):
            self.mFeaturesTable.setItem(i, 0, QTableWidgetItem(feature))
            # headers.append(f'{i + 1}: {feature}')
            headers.append(f'Feature {i + 1}')
        self.mFeaturesTable.setVerticalHeaderLabels(headers)
        self.mFeaturesTable.resizeColumnsToContents()

    @errorHandled(successMessage='updated sample categories')
    def onDatasetTableSave(self, *args):
        filename = self.mFileDataset.filePath()
        if filename == '':
            self.pushParameterMissingSample()
            raise MissingParameterError()

        dump = ClassifierDump(**Utils.pickleLoad(filename))

        categories = list()
        for i, origCategory in enumerate(dump.categories):
            name: QTableWidgetItem = self.mCategoryTable.item(i, 1)
            color: QgsColorButton = self.mCategoryTable.cellWidget(i, 2)
            categories.append(Category(origCategory.value, name.text(), color.color().name()))

        features = list()
        for i, origFeature in enumerate(dump.features):
            name: QTableWidgetItem = self.mFeaturesTable.item(i, 0).text()
            features.append(name)

        # overwrite sample
        dump = ClassifierDump(categories, features, dump.X, dump.y, dump.classifier)
        Utils.pickleDump(dump.__dict__, filename)

    @errorHandled(successMessage=None)
    def onSetTrainSize(self, *args):
        n = self.mAbsoluteSizeValue.value()
        p = self.mRelativeSizeValue.value() / 100.
        for i in range(self.mCategoryTable.rowCount()):
            box: QgsSpinBox = self.mCategoryTable.cellWidget(i, 4)
            ni = n
            if self.mRelativeSizeCheck.isChecked():
                ni = int(round(p * box.maximum()))
            box.setValue(ni)

    @errorHandled(successMessage=None)
    def onSetTestSize(self, *args):
        n = self.mAbsoluteSizeValue.value()
        p = self.mRelativeSizeValue.value() / 100.
        for i in range(self.mCategoryTable.rowCount()):
            box: QgsSpinBox = self.mCategoryTable.cellWidget(i, 5)
            ni = n
            if self.mRelativeSizeCheck.isChecked():
                ni = int(round(p * box.maximum()))
            box.setValue(ni)

    @errorHandled(successMessage=None)
    def onSetSplitSize(self, *args):
        # assign all samples for testing first...
        for i in range(self.mCategoryTable.rowCount()):
            box: QgsSpinBox = self.mCategoryTable.cellWidget(i, 5)
            box.setValue(box.maximum())
        # ...and finally set the correct train sizes, which will correct the test sizes
        self.onSetTrainSize()

    def onViewFile(self):
        files = {
            self.mViewDataset: self.mFileDataset,
            self.mViewTrainingDataset: self.mFileTrainingDataset,
            self.mViewTestDataset: self.mFileTestDataset,
            self.mViewClusteringReport: self.mFileClusteringReport,
            self.mViewTrainingDatasetClustered: self.mFileTrainingDatasetClustered,
            self.mViewTestDatasetClustered: self.mFileTestDatasetClustered,
            self.mViewRankingReport: self.mFileRankingReport,
            self.mViewTrainingDatasetRanked: self.mFileTrainingDatasetRanked,
            self.mViewTestDatasetRanked: self.mFileTestDatasetRanked,
            self.mViewClassifierFitted: self.mFileClassifierFitted,
            self.mViewClassifierPerformanceReport: self.mFileClassifierPerformanceReport,
            self.mViewClassificationPerformanceReport: self.mFileClassificationPerformanceReport
        }

        file: QgsFileWidget = files[self.sender()]
        filename = file.filePath()

        if filename.endswith('.pkl'):
            dump = Utils.pickleLoad(filename)
            filename = filename + '.json'
            Utils.jsonDump(dump, filename)
        self.openWebbrowser(filename)

    def openWebbrowser(self, filename: str):
        if filename == '':
            return

        if exists(filename):
            webbrowser.open_new_tab(filename)

    def pushParameterMissing(self, name: str, message='', runAlgo: str = None):
        if runAlgo is not None:
            message = f"run '{runAlgo}' algorithm first"
        self.mMessageBar.pushInfo(f'Missing parameter ({name})', message)

    def pushParameterMissingLayer(self, name):
        self.pushParameterMissing(name, message='select layer first')

    def pushParameterWrongValue(self, name, message):
        self.mMessageBar.pushInfo(f'Wrong parameter value ({name})', message)

    def tabPath(self, mObj: QWidget) -> str:
        lookup = {
            self.mFileDataset.objectName(): 'Dataset/Creation/Output dataset',
            self.mFileTrainingDataset.objectName(): 'Dataset/Style and Split/Output training dataset',
            self.mFileTestDataset.objectName(): 'Dataset/Style and Split/Output test dataset',
            self.mFileTrainingDatasetClustered.objectName(): 'Feature Selection/Clustering/Selection/Output training dataset (clustered)',
            self.mFileTestDatasetClustered.objectName(): 'Feature Selection/Clustering/Selection/Output test dataset (clustered)',
            self.mFileTrainingDatasetRanked.objectName(): 'Feature Selection/Ranking/Selection/Output training dataset (ranked)',
            self.mFileTestDatasetRanked.objectName(): 'Feature Selection/Ranking/Selection/Output test dataset (ranked)',
            self.mFileClassifierFitted.objectName(): 'Model/Output classifier (fitted)',
            self.mFileClusteringReport.objectName(): 'Feature Selection/Feature Clustering/Cluster Analysis/Output report',
            self.mFileRankingReport.objectName(): 'Feature Selection/Feature Ranking/Rank Analysis/Output report',
            self.mFilePredictedClassification.objectName(): 'Classification/Predict/Predicted classification layer'
        }
        path = lookup.get(mObj.objectName(), '<unknown location>')
        return path
