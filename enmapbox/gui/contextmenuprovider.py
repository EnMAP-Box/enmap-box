from os.path import exists

from PyQt5.QtCore import QObject, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QWidgetAction, QApplication, QAction

from enmapbox.gui.contextmenus import EnMAPBoxAbstractContextMenuProvider
from enmapbox.gui.datasources.datasources import DataSource, RasterDataSource
from enmapbox.gui.datasources.datasourcesets import DataSourceSet
from enmapbox.gui.datasources.manager import DataSourceManager, DataSourceManagerTreeView
from enmapbox.gui.dataviews.docks import Dock, MapDock
from enmapbox.gui.mapcanvas import MapCanvas, CanvasLink
from qgis.core import QgsPointXY, QgsRasterLayer, QgsMapLayerProxyModel, QgsProject, QgsLayerTree, QgsVectorLayer

from qgis.gui import QgisInterface, QgsMapLayerComboBox

from qps.crosshair.crosshair import CrosshairDialog
from qps.speclib.gui.spectrallibraryplotwidget import SpectralProfilePlotModel
from qps.utils import qgisAppQgisInterface, SpatialPoint, SpatialExtent


class EnMAPBoxContextMenuProvider(EnMAPBoxAbstractContextMenuProvider):
    """
    Core context menu provider
    """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def populateMapCanvasMenu(self, menu: QMenu, mapCanvas: MapCanvas, pos: QPoint, point: QgsPointXY):

        action = menu.addAction('Link with other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_basic.svg'))
        action.triggered.connect(lambda: CanvasLink.ShowMapLinkTargets(self))
        action = menu.addAction('Remove links to other maps')
        action.setIcon(QIcon(':/enmapbox/gui/ui/icons/link_open.svg'))
        action.triggered.connect(lambda: self.removeAllCanvasLinks())

        qgisApp = qgisAppQgisInterface()
        b = isinstance(qgisApp, QgisInterface)
        menu.addSeparator()
        m = menu.addMenu('QGIS...')
        m.setIcon(QIcon(r':/images/themes/default/providerQgis.svg'))
        action = m.addAction('Use map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: self.setCenter(SpatialPoint.fromMapCanvasCenter(qgisApp.mapCanvas())))

        action = m.addAction('Set map center')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: qgisApp.mapCanvas().setCenter(
                self.spatialCenter().toCrs(qgisApp.mapCanvas().mapSettings().destinationCrs())))

        action = m.addAction('Use map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: self.setExtent(SpatialExtent.fromMapCanvas(qgisApp.mapCanvas())))

        action = m.addAction('Set map extent')
        action.setEnabled(b)
        if b:
            action.triggered.connect(lambda: qgisApp.mapCanvas().setExtent(
                self.spatialExtent().toCrs(qgisApp.mapCanvas().mapSettings().destinationCrs())))

        menu.addSeparator()
        m = menu.addMenu('Crosshair')

        if mapCanvas.crosshairIsVisible():
            action = m.addAction('Hide')
            action.triggered.connect(lambda: mapCanvas.setCrosshairVisibility(False))
        else:
            action = m.addAction('Show')
            action.triggered.connect(lambda: mapCanvas.setCrosshairVisibility(True))

        action = m.addAction('Style')
        action.triggered.connect(lambda: mapCanvas.setCrosshairStyle(
            CrosshairDialog.getCrosshairStyle(
                crosshairStyle=mapCanvas.crosshairStyle(), mapCanvas=mapCanvas
            )
        ))

        mPxGrid = m.addMenu('Pixel Grid')
        if mapCanvas.mCrosshairItem.crosshairStyle().mShowPixelBorder:
            action = mPxGrid.addAction('Hide')
            action.triggered.connect(lambda: mapCanvas.mCrosshairItem.crosshairStyle().setShowPixelBorder(False))

        mPxGrid.addSeparator()

        rasterLayers = [lyr for lyr in mapCanvas.layers() if isinstance(lyr, QgsRasterLayer) and lyr.isValid()]

        def onShowRasterGrid(layer: QgsRasterLayer):
            self.mCrosshairItem.setVisibility(True)
            self.mCrosshairItem.crosshairStyle().setShowPixelBorder(True)
            self.mCrosshairItem.setRasterGridLayer(layer)

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

        # keep the list short an focus on

        # list each source only once
        all_layers = QgsProject.instance().mapLayers().values()
        all_layers = sorted(all_layers, key=lambda l: not l.title().startswith('[EnMAP-Box]'))

        excepted_layers = []
        sources = []
        for lyr in all_layers:
            if lyr.source() in sources:
                excepted_layers.append(lyr)
            else:
                sources.append(lyr.source())
        cb.setExceptedLayerList(excepted_layers)

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
        action.triggered.connect(lambda: mapCanvas.zoomToPixelScale(spatialPoint=point))

        menu.addSeparator()

        m = menu.addMenu('Save to...')
        action = m.addAction('PNG')
        action.triggered.connect(lambda: mapCanvas.saveMapImageDialog('PNG'))
        action = m.addAction('JPEG')
        action.triggered.connect(lambda: mapCanvas.saveMapImageDialog('JPG'))
        action = m.addAction('Clipboard')
        action.triggered.connect(lambda: QApplication.clipboard().setPixmap(mapCanvas.pixmap()))
        action = menu.addAction('Copy layer paths')
        action.triggered.connect(lambda: QApplication.clipboard().setText('\n'.join(mapCanvas.layerPaths())))

        menu.addSeparator()

        action = menu.addAction('Refresh')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda: mapCanvas.refresh())

        action = menu.addAction('Refresh all layers')
        action.setIcon(QIcon(":/qps/ui/icons/refresh_green.svg"))
        action.triggered.connect(lambda: mapCanvas.refreshAllLayers())

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
                m = menu.addMenu('Add Spectral Library')
                for slw in slws:
                    speclib = slw.speclib()
                    if isinstance(speclib, QgsVectorLayer):
                        a = m.addAction(speclib.name())
                        a.setToolTip(speclib.source())
                        a.triggered.connect(lambda *args, sl=speclib, n=node: node.insertLayer(0, sl))
        menu.addSeparator()
        s = ""

    def populateDataSourceMenu(self,
                               menu: QMenu,
                               treeView: DataSourceManagerTreeView):

        node = treeView.selectedNode()
        dataSources = treeView.selectedDataSources()
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapbox: EnMAPBox = treeView.enmapboxInstance()

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
            a.setEnabled(exists(node.source()))
            a.triggered.connect(lambda *args, src=node: self.onOpenInExplorer(src))

            # todo: implement rename function

            def appendRasterActions(subMenu: QMenu, src: RasterDataSource, target):
                assert isinstance(src, RasterDataSource)
                subAction = subMenu.addAction('Default Colors')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            self.openInMap(s, t, rgb='DEFAULT'))

                b = src.mWavelengthUnits is not None

                subAction = subMenu.addAction('True Color')
                subAction.setToolTip('Red-Green-Blue true colors')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            self.openInMap(s, t, rgb='R,G,B'))
                subAction.setEnabled(b)
                subAction = subMenu.addAction('CIR')
                subAction.setToolTip('nIR Red Green')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            self.openInMap(s, t, rgb='NIR,R,G'))
                subAction.setEnabled(b)

                subAction = subMenu.addAction('SWIR')
                subAction.setToolTip('nIR swIR Red')
                subAction.triggered.connect(lambda *args, s=src, t=target:
                                            self.openInMap(s, t, rgb='NIR,SWIR,R'))
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
                    subAction.triggered.connect(lambda *args, s=src, t=target, rgb=name: self.openInMap(s, t, rgb=rgb))
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
                a.triggered.connect(lambda *args, src=node: self.onSaveAs(src))

                parameters = {TranslateRasterAlgorithm.P_RASTER: node.source()}
                a: QAction = menu.addAction('Translate')
                a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                a.triggered.connect(
                    lambda src: EnMAPBox.instance().showProcessingAlgorithmDialog(
                        TranslateRasterAlgorithm(), parameters, parent=self
                    )
                )

                parameters = {SubsetRasterBandsAlgorithm.P_RASTER: node.source()}
                a: QAction = menu.addAction('Subset bands')
                a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                a.triggered.connect(
                    lambda src: EnMAPBox.instance().showProcessingAlgorithmDialog(
                        SubsetRasterBandsAlgorithm(), parameters, parent=self
                    )
                )

                if splitext(node.source())[1].lower() in ['.tif', '.tiff', '.bsq', '.bil', '.bip']:
                    parameters = {WriteEnviHeaderAlgorithm.P_RASTER: node.source()}
                    a: QAction = m.addAction('Create/update ENVI header')
                    a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                    a.triggered.connect(
                        lambda src: EnMAPBox.instance().showProcessingAlgorithmDialog(
                            WriteEnviHeaderAlgorithm(), parameters, parent=self
                        )
                    )

            elif isinstance(node, VectorDataSource):

                if node.geometryType() not in [QgsWkbTypes.NullGeometry, QgsWkbTypes.UnknownGeometry]:
                    a = m.addAction('Open in new map')
                    a.triggered.connect(lambda *args, s=node: self.openInMap(s, None))

                    sub = m.addMenu('Open in existing map...')
                    if len(mapDocks) > 0:
                        for mapDock in mapDocks:
                            from ..dataviews.docks import MapDock
                            assert isinstance(mapDock, MapDock)
                            a = sub.addAction(mapDock.title())
                            a.triggered.connect(
                                lambda checked, s=node, d=mapDock:
                                self.openInMap(s, d))
                    else:
                        sub.setEnabled(False)

                a = m.addAction('Open Spectral Library Viewer')
                a.triggered.connect(
                    lambda *args, s=node: self.openInSpeclibEditor(node.asMapLayer()))

                a = m.addAction('Open Attribute Table')
                a.triggered.connect(lambda *args, s=node: self.openInAttributeEditor(s.asMapLayer()))

                a = m.addAction('Open in QGIS')
                if isinstance(qgis.utils.iface, QgisInterface):
                    a.triggered.connect(lambda *args, s=node:
                                        self.openInMap(s, QgsProject.instance()))

                a: QAction = m.addAction('Save as')
                a.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
                a.triggered.connect(lambda *args, src=node: self.onSaveAs(src))

            elif isinstance(node, ModelDataSource):
                a = m.addAction('View as JSON')
                a.setIcon(QIcon(':/images/themes/default/mIconFieldJson.svg'))
                a.triggered.connect(lambda *args, node=node: self.onViewPklAsJson(node))

        elif isinstance(node, RasterBandTreeNode):
            # a = m.addAction('Band statistics')
            # a.setEnabled(False)
            # todo: AR call band stats dialog here
            # similar to:
            # a.triggered.connect(lambda: self.runImageStatistics(lyr))
            # See issue #792. Will be implemented for v3.10

            a = m.addAction('Open in new map')
            a.triggered.connect(lambda *args, n=node: self.openInMap(n.rasterSource(), rgb=[n.bandIndex()]))

            sub = m.addMenu('Open in existing map...')
            if len(mapDocks) > 0:
                for mapDock in mapDocks:
                    from ..dataviews.docks import MapDock
                    assert isinstance(mapDock, MapDock)
                    a = sub.addAction(mapDock.title())
                    a.node = node
                    a.mapCanvas = mapDock.mapCanvas()
                    a.triggered.connect(self.onOpenBandInExistingMap)
            else:
                sub.setEnabled(False)
        else:
            aRemove.setEnabled(False)

        if col == 1 and node.value() is not None:
            a = m.addAction('Copy')
            a.triggered.connect(lambda *args, n=node: self.copyNodeValue(n))

        if isinstance(node, TreeNode):
            node.populateContextMenu(m)

        a = m.addAction('Remove all DataSources')
        a.setToolTip('Removes all data source.')
        a.triggered.connect(self.onRemoveAllDataSources)

    def populateDataViewMenu(self, menu: QMenu, dataView: Dock):
        assert isinstance(menu, QMenu)
        if dataView.isVisible():
            a = menu.addAction('Hide View')
            a.triggered.connect(lambda: dataView.setVisible(False))
        else:
            a = menu.addAction('Show View')
            a.triggered.connect(lambda: dataView.setVisible(True))

        a = menu.addAction('Close View')
        a.triggered.connect(lambda: dataView.close())
        return menu
