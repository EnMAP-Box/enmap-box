import unittest

from processing.gui.algorithm_widget import AlgorithmWidget
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QMainWindow, QLineEdit
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsProcessingAlgorithm,
    QgsProcessingProvider,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterString,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
)
from qgis.gui import QgsPanelWidget, QgsProcessingParameterWidgetFactoryInterface, \
    QgsAbstractProcessingParameterWidgetWrapper, QgsGui
from qgis.testing import start_app

start_app()


class CustomStringParameterWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._widget = None
        self.setObjectName(f'CustomWrapper')

    def createWidget(self):
        self._widget = QLineEdit()
        return self._widget

    def setWidgetValue(self, value, context):
        if self._widget is not None and value is not None:
            self._widget.setText(str(value))

    def widgetValue(self, context):
        if self._widget is not None:
            return self._widget.text()
        return None


class CustomStringParameterWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    NAME = 'MyParameterWidget'

    CREATED_WIDGET_WRAPPERS = 0

    def createWidgetWrapper(self, *args, **kwds):
        w = CustomStringParameterWidgetWrapper(*args, **kwds)
        CustomStringParameterWidgetFactory.CREATED_WIDGET_WRAPPERS += 1
        return w

    def clone(self):
        return CustomStringParameterWidgetFactory()

    def parameterType(self):
        return self.NAME


class TestCustomParameterWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._factory = CustomStringParameterWidgetFactory()
        QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls._factory)

    @classmethod
    def tearDownClass(cls):
        QgsGui.processingGuiRegistry().removeParameterWidgetFactory(cls._factory)

    def test_widget_wrapper_creation(self):
        """Test creating widget wrapper for custom parameter."""
        # Create parameter

        param = QgsProcessingParameterString('TEST', 'custom string', optional=False)

        metadata = param.metadata()
        metadata["widget_wrapper"] = {
            "widget_type": (
                CustomStringParameterWidgetFactory.NAME
            )
        }
        param.setMetadata(metadata)
        wrapper_type = Qgis.ProcessingMode.Standard

        # use CustomStringParameterWidgetFactory directly
        self.assertEqual(CustomStringParameterWidgetFactory.CREATED_WIDGET_WRAPPERS, 0)
        wrapper1 = self._factory.createWidgetWrapper(param, wrapper_type)
        self.assertEqual(CustomStringParameterWidgetFactory.CREATED_WIDGET_WRAPPERS, 1)
        self.assertEqual(wrapper1.objectName(), "CustomWrapper")
        self.assertIsInstance(wrapper1, QgsAbstractProcessingParameterWidgetWrapper)
        self.assertIsInstance(wrapper1, CustomStringParameterWidgetWrapper)

        # use the CustomStringParameterWidgetFactory, where we have registered the CustomStringParameterWidgetFactory
        # to
        reg: QgsProcessingGuiRegistry = QgsGui.processingGuiRegistry()

        wrapper2 = reg.createParameterWidgetWrapper(param, wrapper_type)
        self.assertEqual(CustomStringParameterWidgetFactory.CREATED_WIDGET_WRAPPERS, 2)
        self.assertEqual(wrapper2.objectName(), "CustomWrapper")
        self.assertIsInstance(wrapper2, QgsAbstractProcessingParameterWidgetWrapper)

        # this fails, because QgsProcessingGuiRegistry returns the base class
        # QgsAbstractProcessingParameterWidgetWrapper only
        self.assertIsInstance(wrapper2, CustomStringParameterWidgetWrapper)


if __name__ == '__main__':
    unittest.main()
