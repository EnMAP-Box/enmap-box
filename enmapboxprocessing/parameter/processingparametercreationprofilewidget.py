import webbrowser

from qgis.core import QgsMessageLog, Qgis

from qgis.PyQt.QtWidgets import QWidget, QLineEdit, QComboBox, QToolButton
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgsProcessingParameterWidgetFactoryInterface, QgsGui


class ProcessingParameterCreationProfileWidget(QWidget):
    mProfile: QComboBox
    mOptions: QLineEdit
    mWebsite: QToolButton

    PROFILES = [
        ('', ''),
        ('GeoTiff', 'GTiff INTERLEAVE=BAND'),
        ('Compressed GeoTiff', 'GTiff INTERLEAVE=BAND COMPRESS=LZW PREDICTOR=2 BIGTIFF=YES'),
        ('Tiled GeoTiff', 'GTiff INTERLEAVE=BAND TILED=YES'),
        ('Tiled and compressed GeoTiff', 'GTiff INTERLEAVE=BAND COMPRESS=LZW PREDICTOR=2 TILED=YES BIGTIFF=YES'),
        ('ENVI BSQ', 'ENVI INTERLEAVE=BSQ'),
        ('ENVI BIL', 'ENVI INTERLEAVE=BIL'),
        ('ENVI BIP', 'ENVI INTERLEAVE=BIP'),
        ('Virtual Raster', 'VRT')
    ]

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.mProfile.addItems([item[0] for item in self.PROFILES])
        self.mProfile.currentIndexChanged.connect(self.onCurrentIndexChanged)
        self.mWebsite.clicked.connect(self.onWebsiteClicked)

    def onCurrentIndexChanged(self, index):
        _, value = self.PROFILES[index]
        self.mOptions.setText(value)

    def onWebsiteClicked(self):
        _, value = self.PROFILES[self.mProfile.currentIndex()]
        if value.startswith('GTiff'):
            webbrowser.open_new_tab('https://gdal.org/drivers/raster/gtiff.html#creation-options')
        if value.startswith('ENVI'):
            webbrowser.open_new_tab('https://gdal.org/drivers/raster/envi.html')
        if value.startswith('VRT'):
            webbrowser.open_new_tab('https://gdal.org/drivers/raster/vrt.html')


class ProcessingParameterCreationProfileWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):

    def createWidget(self):
        widget = ProcessingParameterCreationProfileWidget()
        return widget

    def setWidgetValue(self, value, context):
        widget = self.wrappedWidget()
        widget.mOptions.setText(value)

    def widgetValue(self):
        widget = self.wrappedWidget()
        return widget.mOptions.text()


class ProcessingParameterCreationProfileWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterCreationProfileWidget'

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        return ProcessingParameterCreationProfileWidgetWrapper(parameter, widget_type)

    @classmethod
    def register(cls):
        success = QgsGui.processingGuiRegistry().addParameterWidgetFactory(cls())
        if success:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} registered', level=Qgis.MessageLevel.Info)
        else:
            QgsMessageLog.logMessage(f'{cls.WIDGET_TYPE} could not be registered', level=Qgis.MessageLevel.Critical)
