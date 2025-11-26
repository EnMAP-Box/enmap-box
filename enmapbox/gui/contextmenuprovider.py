import logging
from os.path import exists, splitext
from typing import List, Union

import numpy as np

import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph as pg
import qgis.utils
from enmapbox.gui.contextmenus import EnMAPBoxAbstractContextMenuProvider
from enmapbox.gui.datasources.datasources import DataSource, RasterDataSource, VectorDataSource, ModelDataSource
from enmapbox.gui.datasources.datasourcesets import DataSourceSet
from enmapbox.gui.datasources.manager import DataSourceManager, DataSourceManagerTreeView
from enmapbox.gui.datasources.metadata import RasterBandTreeNode
from enmapbox.gui.dataviews.dockmanager import DockTreeNode, MapDockTreeNode, DockManagerLayerTreeModelMenuProvider, \
    DockTreeView, LayerTreeNode
from enmapbox.gui.dataviews.docks import Dock, MapDock
from enmapbox.gui.mapcanvas import MapCanvas, CanvasLink
from enmapbox.qgispluginsupport.qps.crosshair.crosshair import CrosshairDialog
from enmapbox.qgispluginsupport.qps.layerproperties import showLayerPropertiesDialog
from enmapbox.qgispluginsupport.qps.models import TreeNode
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibraryplotwidget import SpectralProfilePlotModel
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint, SpatialExtent, findParent
from qgis.PyQt.QtCore import Qt, QObject, QPoint, QModelIndex
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QWidgetAction, QApplication, QAction
from qgis.core import QgsWkbTypes, QgsPointXY, QgsRasterLayer, QgsMapLayerProxyModel, QgsProject, QgsLayerTree, \
    QgsVectorLayer, QgsLayerTreeNode, QgsMapLayer, QgsLayerTreeLayer, QgsLayerTreeGroup
from qgis.gui import QgsMapCanvas, QgisInterface, QgsMapLayerComboBox

logger = logging.getLogger(__name__)


class EnMAPBoxContextMenuProvider(EnMAPBoxAbstractContextMenuProvider):
    """
    Core context menu provider
    """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def populateMapCanvasMenu(self, menu: QMenu, mapCanvas: MapCanvas, pos: QPoint, point: QgsPointXY):

        action = menu.addAction('Link with other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_basic.svg'))
        action.triggered.connect(lambda: CanvasLink.ShowMapLinkTargets(mapCanvas))
        action = menu.addAction('Remove links to other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_open.svg'))
        action.triggered.connect(lambda: mapCanvas.removeAllCanvasLinks())

        from qgis.utils import iface
        b = isinstance(iface, QgisInterface)
        menu.addSeparator()
        m = menu.addMenu('QGIS...')
        m.setIcon(QIcon(r':/images/themes/default/providerQgis.svg'))
        action = m.addAction('Use map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(
                lambda *args, c=mapCanvas: c.setCenter(SpatialPoint.fromMapCanvasCenter(iface.mapCanvas())))

        action = m.addAction('Set map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda *args, c=mapCanvas: iface.mapCanvas().setCenter(
                c.spatialCenter().toCrs(iface.mapCanvas().mapSettings().destinationCrs())))

        action = m.addAction('Use map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(
                lambda *args, c=mapCanvas: c.setExtent(SpatialExtent.fromMapCanvas(iface.mapCanvas())))

        action = m.addAction('Set map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda *args, c=mapCanvas: iface.mapCanvas().setExtent(
                c.spatialExtent().toCrs(iface.mapCanvas().mapSettings().destinationCrs())))

        menu.addSeparator()
        m = menu.addMenu('Crosshair')

        if mapCanvas.crosshairIsVisible():
            action = m.addAction('Hide')
            action.triggered.connect(lambda *args, c=mapCanvas: c.setCrosshairVisibility(False))
        else:
            action = m.addAction('Show')
            action.triggered.connect(lambda *args, c=mapCanvas: c.setCrosshairVisibility(True))

        action = m.addAction('Style')
        action.triggered.connect(lambda *args, c=mapCanvas: c.setCrosshairStyle(
            CrosshairDialog.getCrosshairStyle(
                crosshairStyle=c.crosshairStyle(), mapCanvas=c
            )
        ))

        mPxGrid = m.addMenu('Pixel Grid')
        if mapCanvas.mCrosshairItem.crosshairStyle().mShowPixelBorder:
            action = mPxGrid.addAction('Hide')
            action.triggered.connect(
                lambda *args, c=mapCanvas: c.mCrosshairItem.crosshairStyle().setShowPixelBorder(False))

        mPxGrid.addSeparator()

        rasterLayers = [lyr for lyr in mapCanvas.layers() if isinstance(lyr, QgsRasterLayer) and lyr.isValid()]

        def onShowRasterGrid(layer: QgsRasterLayer):
            mapCanvas.mCrosshairItem.setVisibility(True)
            mapCanvas.mCrosshairItem.crosshairStyle().setShowPixelBorder(True)
            mapCanvas.mCrosshairItem.setRasterGridLayer(layer)

        actionTop = mPxGrid.addAction('Top Raster')
        actionBottom = mPxGrid.addAction('Bottom Raster')

        if len(rasterLayers) == 0:
            actionTop.setEnabled(False)
            actionBottom.setEnabled(False)
        else:
            actionTop.triggered.connect(lambda b, layer=rasterLayers[0]: onShowRasterGrid(layer))
            actionBottom.triggered.connect(lambda b, layer=rasterLayers[-1]: onShowRasterGrid(layer))

        mPxGrid.addSeparator()
        wa = QWidgetAction(mPxGrid)

        cb = QgsMapLayerComboBox()
        cb.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cb.setAllowEmptyLayer(True)
        cb.setProject(mapCanvas.project())

        for i in range(cb.count()):
            lyr = cb.layer(i)
            if lyr == mapCanvas.mCrosshairItem.rasterGridLayer():
                cb.setCurrentIndex(i)
                break
        cb.layerChanged.connect(onShowRasterGrid)
        wa.setDefaultWidget(cb)
        mPxGrid.addAction(wa)

        # action.triggered.connect(lambda b, layer=l: onShowRasterGrid(layer))

        menu.addSeparator()

        action = menu.addAction('Zoom Full')
        action.setIcon(QIcon(':/images/themes/default/mActionZoomFullExtent.svg'))
        action.triggered.connect(mapCanvas.zoomToFullExtent)

        action = menu.addAction('Zoom Native Resolution')
        action.setIcon(QIcon(':/images/themes/default/mActionZoomActual.svg'))
        action.setEnabled(any([lyr for lyr in mapCanvas.layers() if isinstance(lyr, QgsRasterLayer)]))
        action.triggered.connect(lambda *args, c=mapCanvas: c.zoomToPixelScale(spatialPoint=point))

        menu.addSeparator()

        m = menu.addMenu('Save to...')
        action = m.addAction('PNG')
        action.triggered.connect(lambda *args, c=mapCanvas: c.saveMapImageDialog('PNG'))
        action = m.addAction('JPEG')
        action.triggered.connect(lambda *args, c=mapCanvas: c.saveMapImageDialog('JPG'))
        action = m.addAction('Clipboard')
        action.triggered.connect(lambda *args, c=mapCanvas: QApplication.clipboard().setPixmap(c.pixmap()))
        action = menu.addAction('Copy layer paths')
        action.triggered.connect(lambda *args, c=mapCanvas: QApplication.clipboard().setText('\n'.join(c.layerPaths())))

        menu.addSeparator()

        action = menu.addAction('Refresh')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda *args, c=mapCanvas: c.refresh())

        action = menu.addAction('Refresh all layers')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda *args, c=mapCanvas: c.refreshAllLayers())

        action = menu.addAction('Clear')
        action.triggered.connect(mapCanvas.clearLayers)

        menu.addSeparator()
        action = menu.addAction('Set CRS...')
        action.triggered.connect(mapCanvas.setCRSfromDialog)

        action = menu.addAction('Set background color')
        action.triggered.connect(mapCanvas.setBackgroundColorFromDialog)

        action = menu.addAction('Show background layer')
        action.triggered.connect(mapCanvas.setBackgroundLayer)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = self.enmapBox()
        node = mapCanvas.layerTree()
        if isinstance(emb, EnMAPBox) and isinstance(node, QgsLayerTree):

            slws = emb.spectralLibraryWidgets()
            if len(slws) > 0:
                m: QMenu = menu.addMenu('Add Spectral Library')
                m.setToolTipsVisible(True)
                speclibs = []
                for slw in slws:
                    for sl in slw.spectralLibraries():
                        if sl not in speclibs:
                            speclibs.append(sl)

                            a = m.addAction(sl.name())
                            tt = f'Layer {sl.name()} id {sl.id()}<br>Layer Source: {sl.source()}'
                            a.setToolTip(tt)
                            a.triggered.connect(lambda *args, sl=sl, n=node: node.insertLayer(0, sl))
        menu.addSeparator()
        s = ""

    def onAddGroup(self, view: DockTreeView):
        """
        Create a new layer group
        """
        node = view.currentNode()
        selectedLayerNodes = view.selectedLayerNodes()

        newNode = QgsLayerTreeGroup(name='Group')
        if isinstance(node, QgsLayerTree):
            node.insertChildNode(0, newNode)
        elif isinstance(node, (QgsLayerTreeGroup, QgsLayerTreeLayer)):
            parent = node.parent()
            if isinstance(parent, QgsLayerTreeGroup):
                index = parent.children().index(node) + 1
                parent.insertChildNode(index, newNode)

        model = view.layerTreeModel()
        model.removeNodes(selectedLayerNodes)
        for n in selectedLayerNodes:
            newNode.addChildNode(n)

    def populateDataSourceMenu(self,
                               menu: QMenu,
                               treeView: DataSourceManagerTreeView,
                               selectedNodes: List[Union[DataSourceSet, DataSource]]):

        dataSources = [n for n in selectedNodes if isinstance(n, DataSource)]
        srcURIs = [ds.source() for ds in dataSources]

        if len(selectedNodes) > 0:
            node = selectedNodes[0]
        else:
            node = None
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapbox: EnMAPBox = self.enmapBox()
        col = treeView.currentIndex().column()
        DSM: DataSourceManager = self.enmapBox().dataSourceManager()
        if not isinstance(DSM, DataSourceManager):
            return

        mapDocks = []
        if isinstance(enmapbox, EnMAPBox):
            mapDocks = enmapbox.dockManager().docks('MAP')

        aRemove = menu.addAction('Remove')
        if isinstance(node, DataSourceSet):
            assert isinstance(aRemove, QAction)
            aRemove.setToolTip('Removes all datasources from this node')
            aRemove.triggered.connect(lambda *args, n=node, dsm=DSM:
                                      DSM.removeDataSources(n.dataSources()))

        elif isinstance(node, DataSource):
            aRemove.triggered.connect(lambda *args, ds=dataSources, dsm=DSM:
                                      dsm.removeDataSources(ds))
            aCopy = menu.addAction('Copy URI / path')
            aCopy.triggered.connect(lambda *args, u=srcURIs:
                                    QApplication.clipboard().setText('\n'.join(u)))

            a: QAction = menu.addAction('Open in Explorer')
            a.setIcon(QIcon(':/images/themes/default/mIconFolderOpen.svg'))
            a.setEnabled(exists(node.source().split('|')[0]))
            a.triggered.connect(lambda *args, src=node: treeView.onOpenInExplorer(src))

            # todo: implement rename function

            def appendRasterActions(subMenu: QMenu, src: RasterDataSource, target):
                assert isinstance(src, RasterDataSource)
                subAction = subMenu.addAction('Default Colors')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            treeView.openInMap(s, t, rgb='DEFAULT'))

                b = src.mWavelengthUnits is not None

                subAction = subMenu.addAction('True Color')
                subAction.setToolTip('Red-Green-Blue true colors')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            treeView.openInMap(s, t, rgb='R,G,B'))
                subAction.setEnabled(b)
                subAction = subMenu.addAction('CIR')
                subAction.setToolTip('nIR Red Green')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            treeView.openInMap(s, t, rgb='NIR,R,G'))
                subAction.setEnabled(b)

                subAction = subMenu.addAction('SWIR')
                subAction.setToolTip('nIR swIR Red')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            treeView.openInMap(s, t, rgb='NIR,SWIR,R'))
                subAction.setEnabled(b)

                # todo: move to different context menu provider
                from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm
                subMenu2 = subMenu.addMenu('GEE Data Catalog plugin')
                for name, shortNames in CreateSpectralIndicesAlgorithm.sentinel2Visualizations().items():
                    longNames = [CreateSpectralIndicesAlgorithm.LongNameMapping[shortName] for shortName in shortNames]
                    wavelengths = [f'{CreateSpectralIndicesAlgorithm.WavebandMapping[shortName][0]} nm'
                                   for shortName in shortNames]
                    subAction = subMenu2.addAction(name + f' ({" - ".join(wavelengths)})')
                    subAction.setToolTip(' - '.join(longNames))
                    subAction.triggered.connect(
                        lambda *args, s=src, t=target, rgb=name: treeView.openInMap(s, t, rgb=rgb))
                    subAction.setEnabled(b)

            if isinstance(node, RasterDataSource):
                sub = menu.addMenu('Open in new map...')
                appendRasterActions(sub, node, None)

                sub = menu.addMenu('Open in existing map...')
                self.enmapBox()
                if len(mapDocks) > 0:
                    for mapDock in mapDocks:
                        assert isinstance(mapDock, MapDock)
                        subsub = sub.addMenu(mapDock.title())
                        appendRasterActions(subsub, node, mapDock)
                else:
                    SpectralProfilePlotModel
                    sub.setEnabled(False)
                sub = menu.addMenu('Open in QGIS')

                if isinstance(qgis.utils.iface, QgisInterface):
                    appendRasterActions(sub, node, QgsProject.instance())
                else:
                    sub.setEnabled(False)

                from enmapboxprocessing.algorithm.subsetrasterbandsalgorithm import SubsetRasterBandsAlgorithm
                from enmapboxprocessing.algorithm.translaterasteralgorithm import TranslateRasterAlgorithm
                from enmapboxprocessing.algorithm.writeenviheaderalgorithm import WriteEnviHeaderAlgorithm

                # AR: add some useful processing algo shortcuts
                a: QAction = menu.addAction('Save as')
                a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                a.triggered.connect(lambda *args, src=node: treeView.onSaveAs(src))

                parameters = {TranslateRasterAlgorithm.P_RASTER: node.source()}
                a: QAction = menu.addAction('Translate')
                a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                a.triggered.connect(
                    lambda src: EnMAPBox.instance().showProcessingAlgorithmDialog(
                        TranslateRasterAlgorithm(), parameters, parent=treeView
                    )
                )

                parameters = {SubsetRasterBandsAlgorithm.P_RASTER: node.source()}
                a: QAction = menu.addAction('Subset bands')
                a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                a.triggered.connect(
                    lambda src: EnMAPBox.instance().showProcessingAlgorithmDialog(
                        SubsetRasterBandsAlgorithm(), parameters, parent=treeView
                    )
                )

                if splitext(node.source())[1].lower() in ['.tif', '.tiff', '.bsq', '.bil', '.bip']:
                    parameters = {WriteEnviHeaderAlgorithm.P_RASTER: node.source()}
                    a: QAction = menu.addAction('Create/update ENVI header')
                    a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                    a.triggered.connect(
                        lambda src: EnMAPBox.instance().showProcessingAlgorithmDialog(
                            WriteEnviHeaderAlgorithm(), parameters, parent=treeView
                        )
                    )

            elif isinstance(node, VectorDataSource):

                if node.geometryType() not in [QgsWkbTypes.NullGeometry, QgsWkbTypes.UnknownGeometry]:
                    a = menu.addAction('Open in new map')
                    a.triggered.connect(lambda *args, s=node: treeView.openInMap(s, None))

                    sub = menu.addMenu('Open in existing map...')
                    if len(mapDocks) > 0:
                        for mapDock in mapDocks:
                            assert isinstance(mapDock, MapDock)
                            a = sub.addAction(mapDock.title())
                            a.triggered.connect(
                                lambda checked, s=node, d=mapDock:
                                treeView.openInMap(s, d))
                    else:
                        sub.setEnabled(False)
                project = self.enmapBox().project()
                a = menu.addAction('Open Spectral Library Viewer')
                a.triggered.connect(
                    lambda *args, s=node: treeView.openInSpeclibEditor(node.asMapLayer(project=project)))

                a = menu.addAction('Open Attribute Table')
                a.triggered.connect(lambda *args, s=node: treeView.openInAttributeEditor(s.asMapLayer(project=project)))

                a = menu.addAction('Open in QGIS')
                if isinstance(qgis.utils.iface, QgisInterface):
                    a.triggered.connect(lambda *args, s=node:
                                        treeView.openInMap(s, QgsProject.instance()))

                a: QAction = menu.addAction('Save as')
                a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                a.triggered.connect(lambda *args, src=node: treeView.onSaveAs(src))

            elif isinstance(node, ModelDataSource):
                a = menu.addAction('View as JSON')
                a.setIcon(QIcon(':/images/themes/default/mIconFieldJson.svg'))
                a.triggered.connect(lambda *args, node=node: treeView.onViewPklAsJson(node))

        elif isinstance(node, RasterBandTreeNode):
            # a = m.addAction('Band statistics')
            # a.setEnabled(False)
            # todo: AR call band stats dialog here
            # similar to:
            # a.triggered.connect(lambda: self.runImageStatistics(lyr))
            # See issue #792. Will be implemented for v3.10

            a = menu.addAction('Open in new map')
            a.triggered.connect(lambda *args, n=node: treeView.openInMap(n.rasterSource(), rgb=[n.bandIndex()]))

            sub = menu.addMenu('Open in existing map...')
            if len(mapDocks) > 0:
                for mapDock in mapDocks:
                    assert isinstance(mapDock, MapDock)
                    a = sub.addAction(mapDock.title())
                    a.node = node
                    a.mapCanvas = mapDock.mapCanvas()
                    a.triggered.connect(treeView.onOpenBandInExistingMap)
            else:
                sub.setEnabled(False)
        else:
            aRemove.setEnabled(False)

        if col == 1 and node.value() is not None:
            a = menu.addAction('Copy')
            a.triggered.connect(lambda *args, n=node: treeView.copyNodeValue(n))

            # plotting list of values (see issue #668)
            try:
                obj = node.mPyObject
                array = np.array(obj, dtype=float)
                assert array.ndim == 1
                a = menu.addAction('Plot values')
                a.triggered.connect(
                    lambda *args: pg.plot(range(1, len(array) + 1), array).setWindowTitle(f'Value Plot - {node.name()}')
                )
            except Exception as error:
                pass

        # add the node-specific menu actions
        if isinstance(node, TreeNode):
            node.populateContextMenu(menu)

        a = menu.addAction('Remove all DataSources')
        a.setToolTip('Removes all data source.')
        a.triggered.connect(treeView.onRemoveAllDataSources)

    def populateDataViewMenu(self, menu: QMenu, view: DockTreeView, node: QgsLayerTreeNode):

        assert isinstance(menu, QMenu)
        cidx: QModelIndex = view.currentIndex()
        if isinstance(node, DockTreeNode):
            viewNode: DockTreeNode = node
        else:
            viewNode: DockTreeNode = findParent(node, DockTreeNode, checkInstance=True)
        if not isinstance(viewNode, DockTreeNode):
            return

        oldProvider: DockManagerLayerTreeModelMenuProvider = view.menuProvider()
        errors: List[ModuleNotFoundError] = []

        dataView = viewNode.dock

        if dataView.isVisible():
            a = menu.addAction('Hide View')
            a.triggered.connect(lambda: dataView.setVisible(False))
        else:
            a = menu.addAction('Show View')
            a.triggered.connect(lambda: dataView.setVisible(True))

        a = menu.addAction('Close View')
        a.triggered.connect(lambda: dataView.close())

        lyr: QgsMapLayer = None
        canvas: QgsMapCanvas = None
        if isinstance(viewNode, MapDockTreeNode):
            assert isinstance(viewNode.dock, MapDock)
            canvas = viewNode.dock.mCanvas

        selectedLayerNodes = list(set(view.selectedLayerNodes()))

        if isinstance(node, (DockTreeNode, QgsLayerTreeLayer, QgsLayerTreeGroup)):
            actionEdit = menu.addAction('Rename')
            actionEdit.setShortcut(Qt.Key_F2)
            actionEdit.triggered.connect(lambda *args, idx=cidx: view.edit(idx))

        if isinstance(node, MapDockTreeNode) or isinstance(viewNode, MapDockTreeNode) \
                and isinstance(node, (QgsLayerTreeGroup, QgsLayerTreeLayer)):
            action = menu.addAction('Add Group')
            action.setIcon(QIcon(':/images/themes/default/mActionAddGroup.svg'))
            action.triggered.connect(lambda tv=view: self.onAddGroup(view))

        if type(node) is QgsLayerTreeGroup:
            action = menu.addAction('Remove Group')
            action.setToolTip('Remove the layer group')
            action.triggered.connect(
                lambda *arg, nodes=[node]: view.layerTreeModel().removeNodes(nodes))

        if type(node) is QgsLayerTreeLayer:
            # get parent dock node -> related map canvas
            lyr = node.layer()

            if isinstance(lyr, QgsMapLayer):
                try:
                    oldProvider.addMapLayerMenuItems(node, menu, canvas, selectedLayerNodes)
                except ModuleNotFoundError as ex:
                    errors.append(ex)

            if isinstance(lyr, QgsVectorLayer):
                try:
                    oldProvider.addVectorLayerMenuItems(node, menu)
                except ModuleNotFoundError as ex:
                    errors.append(ex)

            if isinstance(lyr, QgsRasterLayer):
                try:
                    oldProvider.addRasterLayerMenuItems(node, menu)
                except ModuleNotFoundError as ex:
                    errors.append(ex)

        elif isinstance(node, DockTreeNode):
            assert isinstance(node.dock, Dock)
            try:
                node.dock.populateContextMenu(menu)
            except ModuleNotFoundError as ex:
                errors.append(ex)

        elif isinstance(node, LayerTreeNode):
            if cidx.column() == 0:
                try:
                    node.populateContextMenu(menu)
                except ModuleNotFoundError as ex:
                    errors.append(ex)
            elif cidx.column() == 1:
                a = menu.addAction('Copy')
                a.triggered.connect(lambda *args, n=node: QApplication.clipboard().setText('{}'.format(n.value())))

        # let layer properties always be the last menu item
        if isinstance(lyr, QgsMapLayer):
            menu.addSeparator()
            action = menu.addAction('Layer properties')
            action.setToolTip('Set layer properties')
            action.triggered.connect(lambda *args, _lyr=lyr, c=canvas: self.showLayerProperties(_lyr, c))

        if len(errors) > 0:
            # show warning for missing modules
            missing = []
            for ex in errors:
                if isinstance(ex, ModuleNotFoundError):
                    missing.append(ex.name)
            if len(missing) > 0:
                msg = 'Failed to create full layer context menu ' \
                      'due to the following missing packages: {}'.format(','.join(missing))

                logger.error(msg)

        return menu

    def showLayerProperties(self, layer: QgsMapLayer, canvas: QgsMapCanvas):
        messageBar = None
        emb = self.enmapBox()
        if isinstance(emb, QgisInterface) and isinstance(layer, QgsVectorLayer):
            messageBar = emb.messageBar()
        showLayerPropertiesDialog(layer, canvas=canvas, messageBar=messageBar,
                                  modal=True, useQGISDialog=False)
