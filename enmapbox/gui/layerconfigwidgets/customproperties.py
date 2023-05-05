import pathlib

from osgeo import gdal, ogr

from enmapbox.qgispluginsupport.qps.layerconfigwidgets.core import QpsMapLayerConfigWidget
from enmapbox.qgispluginsupport.qps.utils import loadUi
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget
from qgis._gui import QgsCodeEditorJson, QgsJsonEditWidget
from qgis.core import QgsRasterLayer, QgsMapLayer
from qgis.gui import QgsMapCanvas, QgsMapLayerConfigWidgetFactory

PROTECTED = [
    'IMAGE_STRUCTURE:INTERLEAVE',
    'DERIVED_SUBDATASETS:DERIVED_SUBDATASET_1_NAME',
    'DERIVED_SUBDATASETS:DERIVED_SUBDATASET_1_DESC'
    ':AREA_OR_POINT'
]

MAJOR_OBJECTS = [gdal.Dataset.__name__, gdal.Band.__name__, ogr.DataSource.__name__, ogr.Layer.__name__]

MDF_GDAL_BANDMETADATA = 'qgs/gdal_band_metadata'


class CustomPropertiesConfigWidgetFactory(QgsMapLayerConfigWidgetFactory):

    def __init__(self):
        super().__init__('Custom Properties', self.icon())

    def supportsLayer(self, layer):
        return True

    def icon(self) -> QIcon:
        return QIcon(':/qps/ui/icons/edit_gdal_metadata.svg')

    def layerPropertiesPagePositionHint(self) -> str:
        return 'mOptsPage_Legend'

    def supportLayerPropertiesDialog(self):
        return True

    def supportsStyleDock(self):
        return False

    def createWidget(self, layer, canvas, dockWidget=True, parent=None):
        w = CustomPropertiesModelConfigWidget(layer, canvas, parent=parent)
        w.setWindowTitle(self.title())
        w.setWindowIcon(self.icon())
        return w

    def title(self) -> str:
        return 'Custom Properties'


class CustomPropertiesModelConfigWidget(QpsMapLayerConfigWidget):

    def __init__(self, layer: QgsMapLayer = None, canvas: QgsMapCanvas = None, parent: QWidget = None):
        if layer is None:
            layer = QgsRasterLayer()
        if canvas is None:
            canvas = QgsMapCanvas()

        super(CustomPropertiesModelConfigWidget, self).__init__(layer, canvas, parent=parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.mCodeEditorJson: QgsCodeEditorJson
        self.mJsonEdit: QgsJsonEditWidget

        text = '{"a":1, "b":[1,2,3]}'
        self.mCodeEditorJson.setText(text)
        self.mJsonEdit.setJsonText(text)
        self.mCodeEditorJson.textChanged.connect(lambda : self.mJsonEdit.setJsonText(self.mCodeEditorJson.text()))
        self.mJsonEdit.setFormatJsonMode(QgsJsonEditWidget.FormatJson.Compact)

    def setLayer(self, layer: QgsMapLayer):
        pass

    def apply(self):
        pass

    def syncToLayer(self, *args):
        pass

