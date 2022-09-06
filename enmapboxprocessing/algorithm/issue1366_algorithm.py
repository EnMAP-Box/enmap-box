from processing.gui.wrappers import WidgetWrapper
from qgis.core import QgsProcessingParameterFile, QgsProcessingAlgorithm
from qgis.gui import QgsFileWidget


class MyAlgorithm(QgsProcessingAlgorithm):

    def displayName(self):
        return 'Issue 1366 Algorithm'

    def name(self):
        return 'Issue1366Algorithm'

    def shortDescription(self):
        return 'dummy'

    def group(self):
        return 'Debugging'

    def groupId(self):
        return 'Debugging'

    def createInstance(self):
        return type(self)()

    def initAlgorithm(self, configuration):

        # add a normal parameter
        self.addParameter(QgsProcessingParameterFile('file1', 'Normal File'))

        # add a parameter with custom widget
        param = QgsProcessingParameterFile('file2', 'Custom File')
        param.setMetadata({'widget_wrapper': {'class': MyWidgetWrapper}})
        self.addParameter(param)

    def processAlgorithm(self, parameters, context, feedback):
        return {}


class MyWidgetWrapper(WidgetWrapper):
    widget: QgsFileWidget

    def createWidget(self):
        return QgsFileWidget()

    def setValue(self, value):
        self.widget.setFilePath(value)

    def value(self):
        return self.widget.filePath()
