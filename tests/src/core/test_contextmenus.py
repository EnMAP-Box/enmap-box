from qgis.PyQt.QtCore import QEvent, Qt, QPointF
from qgis.PyQt.QtGui import QMouseEvent
from qgis.PyQt.QtWidgets import QMenu

from enmapbox.gui.contextmenus import EnMAPBoxAbstractContextMenuProvider, EnMAPBoxContextMenuRegistry
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.testing import EnMAPBoxTestCase
from qgis.core import QgsPointXY
from qgis.gui import QgsMapMouseEvent


class MyProvider(EnMAPBoxAbstractContextMenuProvider):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mCallbackDataView = None
        self.mCallbackMapLayer = None
        self.mCallbackMapCanvas = None
        self.mCallbackDataSource = None

    def populateDataViewMenu(self, *args, **kwds):
        self.mCallbackDataView(*args, **kwds)

    def populateMapLayerMenu(self, *args, **kwds):
        self.mCallbackMapLayer(*args, **kwds)
        pass

    def populateDataSourceMenu(self, *args, **kwds):
        self.mCallbackDataSource(*args, **kwds)

    def populateMapCanvasMenu(self, *args, **kwds):
        self.mCallbackMapCanvas(*args, **kwds)


class test_applications(EnMAPBoxTestCase):

    def test_mapcanvas(self):
        eb = EnMAPBox(load_core_apps=False, load_other_apps=False)

        provider = MyProvider()
        self.assertEqual(provider.enmapBox(), eb)
        EnMAPBoxContextMenuRegistry.instance().addProvider(provider)

        s = ""
        mapDock = eb.createMapDock()

        canvas: MapCanvas = mapDock.mapCanvas()
        m = QMenu()
        pt = QPointF(canvas.width() * 0.5, canvas.height() * 0.5)
        event = QMouseEvent(QEvent.MouseButtonPress, pt, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        event = QgsMapMouseEvent(canvas, event)

        def callback1(menu, canvas, pos, point):
            self.assertIsInstance(menu, QMenu)
            self.assertIsInstance(canvas, MapCanvas)
            self.assertIsInstance(point, QgsPointXY)
            self.assertEqual(pos, QPointF)

        provider.mCallbackMapCanvas = callback1
        canvas.mousePressEvent(event)
        canvas.populateContextMenu(m, event)

        # populate map dock menu
        m = QMenu()

        def callback2(menu, dataView):
            self.assertEqual(menu, m)
            self.assertEqual(dataView, mapDock)

        provider.mCallbackDataView = callback2
        mapDock.populateContextMenu(m)

        self.showGui(eb.ui)
        eb.close()
