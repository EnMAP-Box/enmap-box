import webbrowser

from qgis.PyQt.uic import loadUi

from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtWidgets import QWidget, QLineEdit, QComboBox, QToolButton


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


class ProcessingParameterCreationProfileWidgetWrapper(WidgetWrapper):
    # adopted from C:\source\QGIS3-master\python\plugins\processing\algs\gdal\ui\RasterOptionsWidget.py

    widget: ProcessingParameterCreationProfileWidget

    def createWidget(self):
        # if self.dialogType == DIALOG_MODELER:
        #    raise NotImplementedError()
        # elif self.dialogType == DIALOG_BATCH:
        #    raise NotImplementedError()
        # else:
        return ProcessingParameterCreationProfileWidget()

    def setValue(self, value: str):
        # if self.dialogType == DIALOG_MODELER:
        #    raise NotImplementedError()
        # elif self.dialogType == DIALOG_BATCH:
        #    raise NotImplementedError()
        # else:
        self.widget.mOptions.setText(value)

    def value(self):
        # if self.dialogType == DIALOG_MODELER:
        #    raise NotImplementedError()
        # elif self.dialogType == DIALOG_BATCH:
        #    raise NotImplementedError()
        # else:
        return self.widget.mOptions.text()
