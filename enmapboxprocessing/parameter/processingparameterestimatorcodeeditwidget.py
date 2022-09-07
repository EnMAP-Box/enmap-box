from qgis.PyQt.uic import loadUi

from enmapboxprocessing.algorithm.algorithms import algorithms
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.fitrandomforestclassifieralgorithm import FitRandomForestClassifierAlgorithm
from enmapboxprocessing.algorithm.fitrandomforestregressoralgorithm import FitRandomForestRegressorAlgorithm
from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxprocessing.parameter.processingparametercodeeditwidget import CodeEditWidget
from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtWidgets import QWidget, QComboBox, QTextBrowser
from typeguard import typechecked


@typechecked
class ProcessingParameterEstimatorCodeEdit(QWidget):
    mEstimator: QComboBox
    mCode: CodeEditWidget
    mDescription: QTextBrowser

    Classifier, Regressor = 0, 1

    def __init__(self, estimatorType: int, parent=None):

        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)
        self.estimatorType = estimatorType
        self.initGui()
        self.mEstimator.currentIndexChanged.connect(self.onEstimatorChanged)

    def initGui(self):
        self.algs = list()
        if self.estimatorType == self.Classifier:
            defaultAlg = FitRandomForestClassifierAlgorithm
            for alg in algorithms():
                if isinstance(alg, FitClassifierAlgorithmBase):
                    self.algs.append(alg)
        elif self.estimatorType == self.Regressor:
            defaultAlg = FitRandomForestRegressorAlgorithm
            for alg in algorithms():
                if isinstance(alg, FitRegressorAlgorithmBase):
                    self.algs.append(alg)
        else:
            raise ValueError()
        items = [alg.displayName().replace('Fit ', '') for alg in self.algs]
        self.mEstimator.addItems(items)
        for i, alg in enumerate(self.algs):
            if isinstance(alg, defaultAlg):
                self.mEstimator.setCurrentIndex(i)
        self.onEstimatorChanged()

    def onEstimatorChanged(self):
        alg = self.algs[self.mEstimator.currentIndex()]
        self.mCode.setText(alg.defaultCodeAsString())
        self.mDescription.setText(alg.helpParameterCode())

    def value(self) -> str:
        return self.mCode.value()


@typechecked
class ProcessingParameterEstimatorCodeEditWrapper(WidgetWrapper):
    widget: ProcessingParameterEstimatorCodeEdit

    def createWidget(self):
        raise NotImplementedError()

    def setValue(self, value):
        self.widget.mCode.setText(value)

    def value(self):
        return self.widget.value()


@typechecked
class ProcessingParameterClassifierCodeEditWrapper(ProcessingParameterEstimatorCodeEditWrapper):

    def createWidget(self):
        return ProcessingParameterEstimatorCodeEdit(ProcessingParameterEstimatorCodeEdit.Classifier)


@typechecked
class ProcessingParameterRegressorCodeEditWrapper(ProcessingParameterEstimatorCodeEditWrapper):

    def createWidget(self):
        return ProcessingParameterEstimatorCodeEdit(ProcessingParameterEstimatorCodeEdit.Regressor)
