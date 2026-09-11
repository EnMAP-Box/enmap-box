from qgis.PyQt import sip
from qgis.PyQt.QtWidgets import QWidget, QComboBox, QTextBrowser
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMessageLog, Qgis
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetFactoryInterface, QgsGui

from enmapboxprocessing.algorithm.algorithms import algorithms
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.fitrandomforestclassifieralgorithm import FitRandomForestClassifierAlgorithm
from enmapboxprocessing.algorithm.fitrandomforestregressoralgorithm import FitRandomForestRegressorAlgorithm
from enmapboxprocessing.algorithm.fitregressoralgorithmbase import FitRegressorAlgorithmBase
from enmapboxprocessing.parameter.processingparametercodeeditwidget import CodeEditWidget


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget = None

    def createWidget(self):
        raise NotImplementedError()

    def setWidgetValue(self, value, context):
        if self._widget is not None:
            self._widget.mCode.setText(value)
        else:
            widget = self.wrappedWidget()
            if widget is not None:
                widget.mCode.setText(value)

    def widgetValue(self):
        if self._widget is not None:
            return self._widget.value()
        widget = self.wrappedWidget()
        if widget is not None:
            return widget.value()
        return None


class ProcessingParameterClassifierCodeEditWrapper(ProcessingParameterEstimatorCodeEditWrapper):

    def createWidget(self):
        self._widget = ProcessingParameterEstimatorCodeEdit(ProcessingParameterEstimatorCodeEdit.Classifier)
        return self._widget


class ProcessingParameterRegressorCodeEditWrapper(ProcessingParameterEstimatorCodeEditWrapper):

    def createWidget(self):
        self._widget = ProcessingParameterEstimatorCodeEdit(ProcessingParameterEstimatorCodeEdit.Regressor)
        return self._widget


class ProcessingParameterClassifierCodeEditFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterClassifierCodeEdit'
    _wrappers = []

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        wrapper = ProcessingParameterClassifierCodeEditWrapper(parameter, widget_type)
        sip.transferto(wrapper, None)
        self._wrappers.append(wrapper)
        return wrapper

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)


class ProcessingParameterRegressorCodeEditFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterRegressorCodeEdit'
    _wrappers = []

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        wrapper = ProcessingParameterRegressorCodeEditWrapper(parameter, widget_type)
        sip.transferto(wrapper, None)
        self._wrappers.append(wrapper)
        return wrapper

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)
