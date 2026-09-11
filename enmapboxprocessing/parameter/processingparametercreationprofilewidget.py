import webbrowser

from qgis.PyQt import sip
from qgis.PyQt.QtWidgets import QWidget, QLineEdit, QComboBox, QToolButton
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMessageLog, Qgis
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget = None

    def createWidget(self):
        self._widget = ProcessingParameterCreationProfileWidget()
        return self._widget

    def setWidgetValue(self, value, context):
        if self._widget is not None:
            self._widget.mOptions.setText(value)
        else:
            widget = self.wrappedWidget()
            if widget is not None:
                widget.mOptions.setText(value)

    def widgetValue(self):
        if self._widget is not None:
            return self._widget.mOptions.text()
        widget = self.wrappedWidget()
        if widget is not None:
            return widget.mOptions.text()
        return None


class ProcessingParameterCreationProfileWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    WIDGET_TYPE = 'enmapbox:ProcessingParameterCreationProfileWidget'
    _wrappers = []

    def parameterType(self):
        return self.WIDGET_TYPE

    def createWidgetWrapper(self, parameter, widget_type):
        wrapper = ProcessingParameterCreationProfileWidgetWrapper(parameter, widget_type)
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
