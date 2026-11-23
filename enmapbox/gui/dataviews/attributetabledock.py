from enmapbox.gui.dataviews.docks import Dock
from qgis.core import QgsVectorLayer


class AttributeTableDock(Dock):
    """
    A dock to show a VectorLayer attribute table
    """

    def __init__(self, layer: QgsVectorLayer, *args, **kwds):
        super(AttributeTableDock, self).__init__(*args, **kwds)
        from enmapbox.qgispluginsupport.qps.layerproperties import AttributeTableWidget
        self.attributeTableWidget = AttributeTableWidget(layer)
        self.addWidget(self.attributeTableWidget, 0, 0)
        self.updateTitle(self.attributeTableWidget.windowTitle())
        self.attributeTableWidget.windowTitleChanged.connect(self.updateTitle)

    def updateTitle(self, title: str):
        # we need to get a short name, not the entire title
        self.setTitle(title.split('::')[0].strip())

    def vectorLayer(self) -> QgsVectorLayer:
        return self.attributeTableWidget.mLayer
