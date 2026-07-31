from qgis.core import QgsMessageLog, Qgis
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetFactoryInterface, QgsGui

from enmapboxprocessing.algorithm.algorithms import algorithms
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.fitrandomforestclassifieralgorithm import FitRandomForestClassifierAlgorithm
from enmapboxprocessing.algorithm.fitrandomforestregressoralgorithm import FitRandomForestRegressorAlgorithm
from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxprocessing.parameter.processingparametercodeeditwidget import CodeEditWidget
from qgis.PyQt.QtWidgets import QWidget, QComboBox, QTextBrowser
from qgis.PyQt.uic import loadUi


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


class ProcessingParameterEstimatorCodeEditWrapper(QgsAbstractProcessingParameterWidgetWrapper):
    widget: ProcessingParameterEstimatorCodeEdit

    def createWidget(self):
        raise NotImplementedError()

    def setWidgetValue(self, value, context):
        widget = self.wrappedWidget()
        widget.mCode.setText(value)

    def widgetValue(self):
        widget = self.wrappedWidget()
        return widget.value()


class ProcessingParameterClassifierCodeEditWrapper(ProcessingParameterEstimatorCodeEditWrapper):

    def createWidget(self):
        widget = ProcessingParameterEstimatorCodeEdit(ProcessingParameterEstimatorCodeEdit.Classifier)
        return widget


class ProcessingParameterRegressorCodeEditWrapper(ProcessingParameterEstimatorCodeEditWrapper):

    def createWidget(self):
        widget = ProcessingParameterEstimatorCodeEdit(ProcessingParameterEstimatorCodeEdit.Regressor)
        return widget


class ProcessingParameterClassifierCodeEditFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterClassifierCodeEdit'

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        return ProcessingParameterClassifierCodeEditWrapper(parameter, widget_type)

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)


class ProcessingParameterRegressorCodeEditFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterRegressorCodeEdit'

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        return ProcessingParameterRegressorCodeEditWrapper(parameter, widget_type)

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)
