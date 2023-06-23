from PyQt5.QtWidgets import QMenu

from enmapbox.gui.contextmenus import EnMAPBoxContextMenuProvider
from enmapbox.gui.datasources.datasources import DataSource
from enmapbox.gui.dataviews.docks import Dock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.testing import EnMAPBoxTestCase
from qgis._core import QgsMapLayer, QgsPointXY


class MyProvider(EnMAPBoxContextMenuProvider):

    def __init__(self, callback):
        self.mCallback = callback

    def extendDataViewMenu(self, *args, **kwds):
        self.mCallback(*args, **kwds)

    def extendMapLayerMenu(self, *args, **kwds):
        self.mCallback(*args, **kwds)
        pass

    def extendDataSourceMenu(self, *args, **kwds):
        self.mCallback(*args, **kwds)

    def extendMapCanvasMenu(self, *args, **kwds):
        self.mCallback(*args, **kwds)


class test_applications(EnMAPBoxTestCase):

    def test_mapcanvas(self):
        eb = EnMAPBox(load_core_apps=False, load_other_apps=False)

        myProvider = MyProvider()
        eb.registerContextMenuProvider(myProvider)

        called = False
        def test_canvas(menu, canvas, point):
            self.assertIsInstance(menu, QMenu)
            self.assertIsInstance(canvas, MapCanvas)
            self.assertIsInstance(point, QgsPointXY)
            called = True
        myProvider.mCallback = test_canvas

        mapDock = eb.createMapDock()

        mapDock.mapCanvas()
        eb.close()
