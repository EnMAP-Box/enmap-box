from typing import List, Union

from enmapbox.gui.contextmenuprovider import EnMAPBoxContextMenuProvider
from enmapbox.gui.contextmenus import EnMAPBoxAbstractContextMenuProvider, EnMAPBoxContextMenuRegistry
from enmapbox.gui.datasources.manager import DataSourceManagerTreeView
from enmapbox.gui.dataviews.dockmanager import DockTreeView, DockManagerLayerTreeModelMenuProvider
from enmapbox.gui.dataviews.docks import MapDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.qgispluginsupport.qps.models import TreeNode
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.PyQt.QtCore import QEvent, Qt, QPointF, QPoint, QAbstractItemModel, QRect, QModelIndex
from qgis.PyQt.QtGui import QMouseEvent, QContextMenuEvent, QAction
from qgis.PyQt.QtWidgets import QMenu, QComboBox
from qgis.PyQt.QtWidgets import QWidgetAction
from qgis.core import QgsPointXY, QgsLayerTreeNode, QgsRasterLayer, QgsProject
from qgis.gui import QgsMapMouseEvent

start_app()


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

    def test_context_menu_providers(self):
        eb = EnMAPBox(load_core_apps=False, load_other_apps=False)
        eb.loadExampleData()
        provider = MyProvider()
        self.assertEqual(provider.enmapBox(), eb)
        reg: EnMAPBoxContextMenuRegistry = EnMAPBoxContextMenuRegistry.instance()
        reg.addProvider(provider)
        reg.setRaiseErrors(True)

        mapDock: MapDock = eb.docks(MapDock)[0]

        # populate map dock menu
        m = QMenu()

        def callbackMapCanvas(menu, canvas, pos, point):
            self.assertIsInstance(menu, QMenu)
            self.assertIsInstance(canvas, MapCanvas)
            self.assertIsInstance(point, QgsPointXY)
            self.assertIsInstance(pos, QPoint)
            menu.addAction('callbackMapCanvas')

        def callbackDataView(menu, dataView, node):
            self.assertIsInstance(menu, QMenu)
            self.assertIsInstance(dataView, DockTreeView)
            self.assertIsInstance(node, QgsLayerTreeNode)
            menu.addAction('callbackDataView')

        def callbackDataSource(menu, view, nodes):
            self.assertIsInstance(menu, QMenu)
            self.assertEqual(menu, m)
            self.assertIsInstance(nodes, list)
            for n in nodes:
                self.assertIsInstance(n, TreeNode)
            self.assertEqual(view, eb.dataSourceManagerTreeView())
            menu.addAction('callbackDataSource')

        provider.mCallbackMapCanvas = callbackMapCanvas
        provider.mCallbackDataView = callbackDataView
        provider.mCallbackDataSource = callbackDataSource

        # test canvas menu
        canvas: MapCanvas = mapDock.mapCanvas()

        pt = QPointF(canvas.width() * 0.5, canvas.height() * 0.5)
        event = QMouseEvent(QEvent.MouseButtonPress, pt, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        event = QgsMapMouseEvent(canvas, event)

        canvas.mousePressEvent(event)
        canvas.populateContextMenu(m, event)
        mapDock.populateContextMenu(m)

        def getAllIndices(model: QAbstractItemModel, parent: QModelIndex = QModelIndex()) -> List[QModelIndex]:
            indices = []
            for r in range(model.rowCount(parent)):
                for c in range(model.columnCount(parent)):
                    idx: QModelIndex = model.index(r, c, parent=parent)
                    if idx.isValid():
                        indices.append(idx)
                        indices.extend(getAllIndices(model, parent=idx))
            return indices

        # test DataSourceManagerTreeView menus
        tv: DataSourceManagerTreeView = eb.dataSourceManagerTreeView()
        model: QAbstractItemModel = tv.model()

        indices = getAllIndices(model)

        for idx in indices:
            idx: QModelIndex
            rect: QRect = tv.visualRect(idx)
            pt: QPoint = rect.topLeft() + QPoint(int(rect.width() * 0.5), int(rect.height() * 0.5))

            event = QContextMenuEvent(QContextMenuEvent.Mouse, pt)
            # QApplication.sendEvent(tv, event)
            m.clear()
            tv.populateContextMenu(m)

        # test DockTreeView menus
        tv: DockTreeView = eb.dockTreeView()
        mp: DockManagerLayerTreeModelMenuProvider = tv.menuProvider()
        self.assertIsInstance(mp, DockManagerLayerTreeModelMenuProvider)

        indices = getAllIndices(tv.layerTreeModel())
        for idx in indices:
            tv.setCurrentIndex(idx)
            menu = mp.createContextMenu()
            self.assertIsInstance(menu, QMenu)

        EnMAPBoxContextMenuRegistry.instance().removeProvider(provider)

        self.showGui(eb.ui)
        eb.close()

    def test_raster_grid_combo(self):
        canvas = MapCanvas()
        project = QgsProject()
        canvas.setProject(project)

        # Add some dummy raster layers
        l1 = QgsRasterLayer("None", "Layer 1", "gdal")
        l2 = QgsRasterLayer("None", "Layer 2", "gdal")
        project.addMapLayers([l1, l2])
        canvas.setLayers([l1, l2])

        LAYERS = {lyr.id(): lyr for lyr in project.mapLayers().values()}

        provider = EnMAPBoxContextMenuProvider()
        menu = QMenu()
        provider.populateMapCanvasMenu(menu, canvas, QPoint(0, 0), QgsPointXY(0, 0))

        def get_menu(menu: QMenu, submenu: List[str]) -> Union[QAction, None]:
            current_menu = menu

            for n in submenu:
                for a in current_menu.actions():
                    if a.text() == n:
                        if n == submenu[-1]:
                            return a

                        current_menu = a.menu()
                        if current_menu is None:
                            return None
                        break
                else:
                    return None

        m = get_menu(menu, ['Crosshair', 'Pixel Grid'])

        self.assertIsInstance(m, QAction)
        # Find the combo box
        cb = None
        for a in m.menu().actions():
            if isinstance(a, QWidgetAction):
                cb = a.defaultWidget()

        self.assertIsInstance(cb, QComboBox)
        for i in range(1, cb.count()):
            lid = cb.itemData(i, Qt.UserRole)
            tt = cb.itemData(i, Qt.ToolTipRole)
            self.assertTrue(lid in LAYERS)
            self.assertTrue(lid in tt)
