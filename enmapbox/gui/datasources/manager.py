import logging
import os
import pickle
import re
import warnings
import webbrowser
from os.path import dirname, exists, sep
from pathlib import Path
from typing import Any, Dict, List, Union, Optional

import numpy as np

from enmapbox.gui.datasources.datasourcesets import DataSourceSet, FileDataSourceSet, ModelDataSourceSet, \
    RasterDataSourceSet, VectorDataSourceSet
from enmapbox.gui.utils import enmapboxUiPath
from enmapbox.qgispluginsupport.qps.layerproperties import defaultRasterRenderer
from enmapbox.qgispluginsupport.qps.models import PyObjectTreeNode, TreeModel, TreeNode, TreeView
from enmapbox.qgispluginsupport.qps.utils import bandClosestToWavelength, defaultBands, loadUi
from enmapbox.typeguard import typechecked
from qgis.PyQt.QtCore import pyqtSignal, QAbstractItemModel, QItemSelectionModel, QMimeData, \
    QModelIndex, QSortFilterProxyModel, Qt, QTimer, QUrl
from qgis.PyQt.QtGui import QContextMenuEvent, QDesktopServices
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAbstractItemView, QAction, QApplication, QDialog, QMenu, QTreeView, QWidget
from qgis.core import Qgis, QgsDataItem, QgsLayerItem, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsMapLayer, \
    QgsMimeDataUtils, QgsProject, QgsProviderSublayerDetails, QgsRasterDataProvider, \
    QgsRasterLayer, QgsRasterRenderer, QgsVectorLayer, QgsMapLayerType, QgsIconUtils
from qgis.core import QgsProviderRegistry
from qgis.gui import QgisInterface, QgsDockWidget, QgsMapCanvas
from .datasources import DataSource, FileDataSource, LayerItem, ModelDataSource, RasterDataSource, SpatialDataSource, \
    VectorDataSource
from .metadata import RasterBandTreeNode
from ..dataviews.docks import Dock
from ..mapcanvas import MapCanvas
from ..mimedata import extractMapLayers, fromDataSourceList, MDF_URILIST, QGIS_URILIST_MIMETYPE
from ...qgispluginsupport.qps.speclib.core import is_spectral_library
from ...qgispluginsupport.qps.subdatasets import SubDatasetSelectionDialog, subLayerDetails

logger = logging.getLogger(__name__)


class DataSourceManager(TreeModel):
    sigDataSourcesRemoved = pyqtSignal(list)
    sigDataSourcesAdded = pyqtSignal(list)

    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)
        self.mRasters: RasterDataSourceSet = RasterDataSourceSet()
        self.mVectors: VectorDataSourceSet = VectorDataSourceSet()
        self.mModels: ModelDataSourceSet = ModelDataSourceSet()
        self.mFiles: FileDataSourceSet = FileDataSourceSet()
        self.rootNode().appendChildNodes([self.mRasters, self.mVectors, self.mModels, self.mFiles])
        self.mProject: QgsProject = QgsProject.instance()

        QgsProject.instance().layersWillBeRemoved.connect(self.onQGISLayerWillBeRemoved)

        self.mNodeUpdateExceptions: List[str] = []
        self.mUpdateTimer: QTimer = QTimer()
        self.mUpdateTimer.setInterval(2000)
        self.mUpdateTimer.timeout.connect(self.updateSourceNodes)
        self.mUpdateTimer.start()
        self.mUpdateState: dict = dict()

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.mEnMAPBoxInstance: EnMAPBox = None

    def __len__(self):
        return len(self.dataSources())

    def enmapBoxInstance(self):
        return self.mEnMAPBoxInstance

    def setEnMAPBoxInstance(self, enmapbox):
        self.mEnMAPBoxInstance = enmapbox
        self.mProject = enmapbox.project()

    def onQGISLayerWillBeRemoved(self, layer_ids: List[str]):
        # remove any source that refers to the layer to be deleted soon
        to_remove = []
        for source in self.dataSources():
            if isinstance(source, LayerItem) and source.layerId() in layer_ids:
                to_remove.append(source)

        if len(to_remove) > 0:
            self.removeDataSources(to_remove)

    def dropMimeData(self, mimeData: QMimeData, action, row: int, column: int, parent: QModelIndex):

        assert isinstance(mimeData, QMimeData)

        result = False
        toAdd = []
        if action in [Qt.MoveAction, Qt.CopyAction]:
            # collect nodes
            nodes = []

            # add new data from external sources
            from enmapbox.gui.mimedata import MDF_QGIS_LAYERTREEMODELDATA
            if mimeData.hasFormat(MDF_URILIST):
                for url in mimeData.urls():
                    toAdd.extend(DataSourceFactory.create(url))

            # add data dragged from QGIS
            elif mimeData.hasFormat(MDF_QGIS_LAYERTREEMODELDATA) or mimeData.hasFormat(QGIS_URILIST_MIMETYPE):

                lyrs = extractMapLayers(mimeData, project=self.project())
                toAdd.extend(DataSourceFactory.create(lyrs))

        added = []
        if len(toAdd) > 0:
            added = self.addDataSources(toAdd)

        return len(added) > 0

    def mimeData(self, indexes: list) -> QMimeData:
        indexes = sorted(indexes)
        if len(indexes) == 0:
            return None

        bandNodes: List[RasterBandTreeNode] = []
        dataSources: List[DataSource] = []
        for node in self.indexes2nodes(indexes):
            if isinstance(node, DataSource):
                dataSources.append(node)
            elif isinstance(node, DataSourceSet):
                dataSources.extend(node.dataSources())
            elif isinstance(node, RasterBandTreeNode):
                bandNodes.append(node)

        mimeData = QMimeData()

        dataSources = list(set(dataSources))
        sourceList = [d.source() for d in dataSources]

        if len(dataSources) > 0:
            mdf = fromDataSourceList(dataSources)
            for f in mdf.formats():
                mimeData.setData(f, mdf.data(f))

            if len(mimeData.formats()) > 0:
                return mimeData

        bandInfo = list()
        for node in bandNodes:
            node: RasterBandTreeNode
            ds: RasterDataSource = node.rasterSource()
            if isinstance(ds, RasterDataSource):
                source = ds.dataItem().path()
                provider = ds.dataItem().providerKey()
                band = node.mBandIndex
                # baseName = '{}:{}'.format(ds.name(), node.name())
                baseName = ds.name()
                bandInfo.append((source, baseName, provider, band))

        if len(bandInfo) > 0:
            from enmapbox.gui.mimedata import MDF_RASTERBANDS
            mimeData.setData(MDF_RASTERBANDS, pickle.dumps(bandInfo))

        urls = [QUrl.fromLocalFile(s) if os.path.isfile(s) else QUrl(s) for s in sourceList]
        if len(urls) > 0:
            mimeData.setUrls(urls)
        return mimeData

    def mimeTypes(self):
        # specifies the mime types handled by this model
        types = []
        # types.append(MDF_DATASOURCETREEMODELDATA)
        from enmapbox.gui.mimedata import MDF_QGIS_LAYERTREEMODELDATA, QGIS_URILIST_MIMETYPE, MDF_URILIST
        types.append(MDF_QGIS_LAYERTREEMODELDATA)
        types.append(QGIS_URILIST_MIMETYPE)
        types.append(MDF_URILIST)
        return types

    def clear(self):
        """
        Removes all data sources
        """
        self.removeDataSources(self.dataSources())

    def importQGISLayers(self):
        """
        Adds datasources known to QGIS which do not exist here
        """
        layers = []

        from qgis.utils import iface
        if isinstance(iface, QgisInterface):
            root = iface.layerTreeView().layerTreeModel().rootGroup()
            assert isinstance(root, QgsLayerTreeGroup)

            for layerTree in root.findLayers():
                assert isinstance(layerTree, QgsLayerTreeLayer)
                s = ""
                grp = layerTree
                # grp.setCustomProperty('nodeHidden', 'true' if bHide else 'false')
                lyr = layerTree.layer()

                if isinstance(lyr, QgsMapLayer) and lyr.isValid() and not grp.customProperty('nodeHidden'):
                    layers.append(layerTree.layer())

        if len(layers) > 0:
            self.addDataSources(DataSourceFactory.create(layers))

    def dataSourceSets(self) -> List[DataSourceSet]:
        return [c for c in self.rootNode().childNodes() if isinstance(c, DataSourceSet)]

    def sources(self, *args):
        warnings.warn(DeprecationWarning('Use .dataSources() instead.'), stacklevel=2)
        return self.dataSources(*args)

    def sourceLayers(self) -> List[QgsMapLayer]:
        """
        Returns layers that cannot be loaded by uri + provider strings. So far used for "memory" sources only
        :return: QgsMapLayer
        :rtype:
        """
        # memory layers cannot be loaded by URI. we need a pointer to access them in drag and drop operations
        layers = []
        for ds in self.dataSources():
            dataItem = ds.dataItem()
            if isinstance(dataItem, LayerItem) and dataItem.hasReferenceLayer():
                if lyr := dataItem.referenceLayer():
                    layers.append(lyr)
        return layers

    def dataSources(self, filter=None) -> List[DataSource]:
        dList = list()
        if isinstance(filter, list):
            for f in filter:
                dList.extend(self.dataSources(filter=f))
        else:
            for ds in self.dataSourceSets():
                dList.extend(ds.dataSources())

            if filter:
                from .datasources import LUT_DATASOURCETYPES, DataSourceTypes
                assert filter in LUT_DATASOURCETYPES.keys(), f'Unknown datasource filter "{filter}"'
                if filter == DataSourceTypes.SpectralLibrary:
                    dList = [ds for ds in dList if isinstance(ds, VectorDataSource) and ds.isSpectralLibrary()]
                else:
                    cls = LUT_DATASOURCETYPES[filter]
                    dList = [ds for ds in dList if isinstance(ds, cls)]
        return dList

    def findDataSources(self, inputs) -> List[DataSource]:
        if not isinstance(inputs, list):
            inputs = [inputs]
        allDataSources = self.dataSources()

        foundSources = []
        for input in inputs:

            if isinstance(input, DataSource) and input in allDataSources:
                foundSources.append(allDataSources[allDataSources.index(input)])  # return reference in own list
            elif isinstance(input, QgsMapLayer):

                for ds in allDataSources:
                    dataItem = ds.dataItem()
                    if isinstance(ds, SpatialDataSource) \
                            and dataItem.path() == input.source() \
                            and dataItem.providerKey() == input.providerType():
                        foundSources.append(ds)
            elif isinstance(input, str):
                for ds in allDataSources:
                    if ds.dataItem().path() == input:
                        foundSources.append(ds)

        return foundSources

    def removeSources(self, *args, **kwds):
        warnings.warn('Use .removeDataSources', DeprecationWarning, stacklevel=2)

        return self.removeDataSources(*args, **kwds)

    def updateSourceNodes(self):
        self.mUpdateTimer.stop()
        try:
            for source in self.dataSources():
                assert isinstance(source, DataSource)
                sid = source.source()

                # save a state that changes with modifications, e.g. modification time
                updateState = None
                uri = source.source()
                lyr = None
                dataItem: QgsDataItem = source.dataItem()

                filepath = uri.split('|')[0]
                if os.path.isfile(filepath):
                    updateState = Path(filepath).stat().st_mtime_ns
                else:
                    # not a file source
                    for lyr in self.project().mapLayers().values():
                        if lyr.source() == uri:
                            if isinstance(lyr, QgsVectorLayer):
                                updateState = [lyr.isValid(), lyr.name(), lyr.featureCount(), lyr.geometryType(),
                                               is_spectral_library(lyr)]
                            elif isinstance(lyr, QgsRasterLayer):
                                updateState = [lyr.bandCount(), lyr.height(), lyr.width()]
                            else:
                                # do not update
                                s = ""

                oldInfo = self.mUpdateState.get(sid, None)
                if oldInfo is None:
                    self.mUpdateState[sid] = updateState
                    source.updateNodes()
                elif oldInfo != updateState:
                    self.mUpdateState[sid] = updateState
                    if isinstance(dataItem, LayerItem):
                        if dataItem.mapLayerType() == QgsMapLayerType.VectorLayer and isinstance(lyr, QgsVectorLayer):
                            if updateState[-1]:
                                # is spectral library
                                icon = QIcon(r':/qps/ui/icons/speclib.svg')
                            else:
                                icon = QgsIconUtils.iconForLayer(lyr)
                            dataItem.setIcon(icon)
                    source.updateNodes()
        except Exception as ex:
            info = str(ex)
            if info not in self.mNodeUpdateExceptions:
                self.mNodeUpdateExceptions.append(info)
                info += "\n This warning will not be shown again."
                logger.error(info)
            pass
        self.mUpdateTimer.start()

    def removeDataSources(self,
                          dataSources: Union[DataSource, List[DataSource]]) -> List[DataSource]:

        ownedSources = self.findDataSources(dataSources)
        removed = []

        for dsSet in self.dataSourceSets():
            removed.extend(dsSet.removeDataSources(ownedSources))
        if len(removed) > 0:
            self.sigDataSourcesRemoved.emit(removed)
        return removed

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemIsDropEnabled

        flags = super(DataSourceManager, self).flags(index)
        node = index.data(Qt.UserRole)
        if isinstance(node, RasterBandTreeNode):
            s = ""
        if isinstance(node, (DataSource, RasterBandTreeNode)):
            flags = flags | Qt.ItemIsDragEnabled
        return flags

    def addSources(self, *args, **kwds):
        warnings.warn(DeprecationWarning('Use addDataSources instead'), stacklevel=2)
        self.addDataSources(*args, **kwds)

    def addSource(self, *args, **kwds):
        warnings.warn(DeprecationWarning('Use addDataSources instead'), stacklevel=2)
        self.addDataSources(*args, **kwds)

    def project(self) -> QgsProject:
        return self.mProject

    def addDataSources(self,
                       sources: Union[DataSource, List[DataSource], Any],
                       name: str = None,
                       show_dialogs: bool = True) -> List[DataSource]:
        sources = DataSourceFactory.create(sources, name=name, project=self.project(), show_dialogs=show_dialogs)
        if isinstance(sources, DataSource):
            sources = [sources]

        added = []
        for source in sources:
            for sourceSet in self.dataSourceSets():
                if sourceSet.isValidSource(source):
                    newSources = sourceSet.addDataSources(source)
                    if len(newSources) > 0:
                        added.extend(newSources)
                        break

        if len(added) > 0:
            self.sigDataSourcesAdded.emit(added)
            self.updateSourceNodes()
        return added


class DataSourceManagerProxyModel(QSortFilterProxyModel):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.setRecursiveFilteringEnabled(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)


class DataSourceManagerTreeView(TreeView):
    """
    A TreeView to show EnMAP-Box Data Sources
    """
    sigPopulateContextMenu = pyqtSignal(QMenu, TreeNode)

    def __init__(self, *args, **kwds):
        super(DataSourceManagerTreeView, self).__init__(*args, **kwds)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def setModel(self, model: QAbstractItemModel):
        super().setModel(model)

    def onRowsInserted(self, parent: QModelIndex, first: int, last: int):
        super().onRowsInserted(parent, first, last)

        node = parent.data(Qt.UserRole)
        n = last - first + 1
        # expand if this was the first added datasource
        if isinstance(node, DataSourceSet) and node.childCount() - n <= 0:
            self.expand(parent)

        # select added row
        idx = self.model().index(last, 0, parent=parent)
        self.selectionModel().select(idx, QItemSelectionModel.ClearAndSelect)

    def dataSourceManager(self) -> DataSourceManager:
        model = self.model()
        if isinstance(model, QSortFilterProxyModel):
            model = model.sourceModel()
        return model

    def enmapboxInstance(self):
        dsm = self.dataSourceManager()
        if isinstance(dsm, DataSourceManager):
            return dsm.enmapBoxInstance()
        return None

    def contextMenuEvent(self, event: QContextMenuEvent):
        """
        Creates and shows the context menu created with a right-mouse-click.
        :param event: QContextMenuEvent
        """

        assert isinstance(event, QContextMenuEvent)

        m: QMenu = QMenu()
        m.setToolTipsVisible(True)
        self.populateContextMenu(m)
        m.exec_(self.viewport().mapToGlobal(event.pos()))

    def populateContextMenu(self, menu: QMenu):
        from ..contextmenus import EnMAPBoxContextMenuRegistry
        # backward compatibility, will be removed
        nodes = self.selectedNodes()
        if len(nodes) > 0:
            self.sigPopulateContextMenu.emit(menu, nodes[0])

        EnMAPBoxContextMenuRegistry.instance().populateDataSourceMenu(menu, self, nodes)

        # backward compatibility, will be removed
        if len(nodes) > 0:
            self.sigPopulateContextMenu.emit(menu, nodes[0])

    def copyNodeValue(self, node):

        if not isinstance(node, TreeNode):
            return

        mimeData = QMimeData()
        if isinstance(node, PyObjectTreeNode):

            obj = node.mPyObject
            if isinstance(obj, np.ndarray):
                mimeData.setText(str(obj.tolist()))
            else:
                mimeData.setText(str(obj))
        else:
            mimeData.setText(str(node.value()))

        QApplication.clipboard().setMimeData(mimeData)

    def onOpenBandInExistingMap(self):
        action: QAction = self.sender()
        node: RasterBandTreeNode = action.node
        mapCanvas: QgsMapCanvas = action.mapCanvas
        self.openInMap(node.rasterSource(), mapCanvas, [node.bandIndex()])

    def openInMap(self,
                  dataSource: Union[VectorDataSource, RasterDataSource, QgsMapLayer],
                  target: Union[None, QgsMapCanvas, QgsProject, Dock] = None,
                  rgb=None,
                  sampleSize: int = None) -> Optional[QgsMapLayer]:
        """
        Add a SpatialDataSource as QgsMapLayer to a mapCanvas.
        :param target:
        :param sampleSize:
        :param dataSource: SpatialDataSource
        :param rgb:
        """
        from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm

        if sampleSize is None:
            sampleSize = int(QgsRasterLayer.SAMPLE_SIZE)

        lyr = None
        if isinstance(dataSource, (VectorDataSource, RasterDataSource)):
            # loads the layer with the default style (wherever it is defined)
            lyr = dataSource.asMapLayer()
        elif isinstance(dataSource, QgsMapLayer):
            lyr = dataSource

        if not isinstance(lyr, QgsMapLayer):
            return None

        from ..dataviews.docks import MapDock
        LOAD_DEFAULT_STYLE: bool = isinstance(rgb, str) and re.search('DEFAULT', rgb, re.I)

        if target is None:
            emb = self.enmapboxInstance()
            from enmapbox.gui.enmapboxgui import EnMAPBox
            if not isinstance(emb, EnMAPBox):
                return None
            dock = emb.createDock('MAP')

            assert isinstance(dock, MapDock)
            target = dock.mapCanvas()

        if isinstance(target, MapDock):
            target = target.mapCanvas()

        assert isinstance(target, (QgsMapCanvas, QgsProject))

        if isinstance(lyr, QgsRasterLayer):
            if LOAD_DEFAULT_STYLE:
                lyr.setRenderer(defaultRasterRenderer(lyr))
            elif isinstance(lyr.dataProvider(), QgsRasterDataProvider) and lyr.dataProvider().name() == 'gdal':

                r = lyr.renderer()
                if isinstance(r, QgsRasterRenderer):
                    bandIndices: List[int] = None
                    if isinstance(rgb, str):
                        if LOAD_DEFAULT_STYLE:
                            bandIndices = defaultBands(lyr)
                        else:
                            if rgb in CreateSpectralIndicesAlgorithm.sentinel2Visualizations():
                                shortNames = CreateSpectralIndicesAlgorithm.sentinel2Visualizations()[rgb]
                                wavelengths = [CreateSpectralIndicesAlgorithm.WavebandMapping[shortName][0]
                                               for shortName in shortNames]
                                bandIndices = [bandClosestToWavelength(lyr, wavelength) for wavelength in wavelengths]
                            else:
                                bandIndices = [bandClosestToWavelength(lyr, s) for s in rgb.split(',')]

                    elif isinstance(rgb, list):
                        bandIndices = rgb

                    if isinstance(bandIndices, list):
                        r = defaultRasterRenderer(lyr, bandIndices=bandIndices, sampleSize=sampleSize)
                        r.setInput(lyr.dataProvider())
                        lyr.setRenderer(r)

                        if len(bandIndices) == 1:
                            name = lyr.name()
                            # todo: change name?
                            # name = f'{name}:{[b+1 for b in bandIndices]}'
                            # name = f'{lyr.name()}:{lyr.dataProvider().displayBandName(bandIndices[0])}'
                            lyr.setName(name)

        elif isinstance(lyr, QgsVectorLayer):

            pass

        if isinstance(target, MapCanvas):
            target.layerTree().insertLayer(0, lyr)

        elif isinstance(target, QgsProject):
            target.addMapLayer(lyr)

        return lyr

    def onSaveAs(self, dataSource: DataSource):
        """
        Saves Vectors/Raster sources
        """
        from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm

        emb = self.enmapboxInstance()
        if emb is None:
            return

        if isinstance(dataSource, RasterDataSource):
            parameters = {SaveRasterAsAlgorithm.P_RASTER: dataSource.source()}
            dlg = emb.showProcessingAlgorithmDialog(SaveRasterAsAlgorithm(), parameters, parent=self)

        elif isinstance(dataSource, VectorDataSource):
            parameters = dict(INPUT=dataSource.source())
            dlg = emb.showProcessingAlgorithmDialog('native:savefeatures', parameters, parent=self)
            s = ""

    @typechecked
    def onOpenInExplorer(self, dataSource: DataSource):
        """Open source in system file explorer."""
        import platform
        filename = dataSource.source()

        # isolate filename; remove '|' options (see #678)
        filename = filename.split('|')[0]

        if not exists(filename):
            return

        system = platform.system()

        if system == 'Windows':
            import subprocess
            filename = filename.replace('/', sep)
            cmd = rf'explorer.exe /select,"{filename}"'
            subprocess.Popen(cmd)
        else:
            url = QUrl.fromLocalFile(dirname(filename))
            QDesktopServices.openUrl(url)

    @typechecked
    def onViewPklAsJson(self, modelDataSource: ModelDataSource):
        """Convert PKL file to JSON sidecar file and open it in the default browser."""
        from enmapboxprocessing.utils import Utils
        filenamePkl = modelDataSource.source()
        filenameJson = filenamePkl + '.json'
        dump = Utils.pickleLoad(filenamePkl)
        Utils.jsonDump(dump, filenameJson)
        webbrowser.open_new_tab(filenameJson)

    def addDataSourceByDialog(self):
        """
        Shows a fileOpen dialog to select new data sources
        :return:
        """
        emb = self.enmapboxInstance()
        if emb:
            emb.openAddDataSourceDialog()

    def onRemoveAllDataSources(self):
        dsm: DataSourceManager = self.dataSourceManager()
        if dsm:
            dsm.clear()

    def selectedDataSources(self) -> List[DataSource]:

        sources = []
        for n in self.selectedNodes():
            if isinstance(n, DataSource) and n not in sources:
                sources.append(n)
        return sources

    def openInSpeclibEditor(self, speclib: QgsVectorLayer):
        """
        Opens a SpectralLibrary in a new SpectralLibraryDock
        :param speclib: SpectralLibrary

        """
        from enmapbox.gui.enmapboxgui import EnMAPBox
        from enmapbox.gui.dataviews.docks import SpectralLibraryDock

        emb = self.enmapboxInstance()
        if isinstance(emb, EnMAPBox):
            emb.createDock(SpectralLibraryDock, speclib=speclib)

    def openInAttributeEditor(self, vectorLayer: QgsVectorLayer):
        from enmapbox.gui.dataviews.docks import AttributeTableDock
        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = self.enmapboxInstance()
        if isinstance(emb, EnMAPBox) and isinstance(vectorLayer, QgsVectorLayer):
            emb.dockManager().createDock(AttributeTableDock, layer=vectorLayer)


class DataSourceManagerPanelUI(QgsDockWidget):
    def __init__(self, parent=None):
        super(DataSourceManagerPanelUI, self).__init__(parent)
        loadUi(enmapboxUiPath('datasourcemanagerpanel.ui'), self)
        self.mDataSourceManager: DataSourceManager = None
        self.mDataSourceManagerProxyModel: DataSourceManagerProxyModel = DataSourceManagerProxyModel()
        assert isinstance(self.mDataSourceManagerTreeView, DataSourceManagerTreeView)
        self.mDataSourceManagerTreeView.setUniformRowHeights(True)
        self.mDataSourceManagerTreeView.setDragDropMode(QAbstractItemView.DragDrop)

        self.btnCollapse.clicked.connect(lambda: self.mDataSourceManagerTreeView.expandSelectedNodes(False))
        self.btnExpand.clicked.connect(lambda: self.mDataSourceManagerTreeView.expandSelectedNodes(True))

        # init actions
        self.actionAddDataSource.triggered.connect(lambda: self.mDataSourceManagerTreeView.addDataSourceByDialog())
        self.actionRemoveDataSource.triggered.connect(
            lambda: self.mDataSourceManager.removeDataSources(self.selectedDataSources()))
        self.actionRemoveDataSource.setEnabled(False)  # will be enabled with selection of node

        # self.mDataSourceManager.exportSourcesToQGISRegistry(showLayers=True)
        self.actionSyncWithQGIS.triggered.connect(self.onSyncToQGIS)

        self.tbFilterText.textChanged.connect(self.setFilter)
        # self.tbFilterText.hide()  # see #167
        # hasQGIS = qgisAppQgisInterface() is not None
        # self.actionSyncWithQGIS.setEnabled(hasQGIS)
        grp = QgsProject.instance().layerTreeRoot()
        grp.addedChildren.connect(lambda *args: self.updateActions())
        grp.removedChildren.connect(lambda *args: self.updateActions())
        self.initActions()
        self.updateActions()

    def dataSourceManagerTreeView(self) -> DataSourceManagerTreeView:
        return self.mDataSourceManagerTreeView

    def setFilter(self, pattern: str):
        self.mDataSourceManagerProxyModel.setFilterWildcard(pattern)

    def onSyncToQGIS(self, *args):
        if isinstance(self.mDataSourceManager, DataSourceManager):
            self.mDataSourceManager.importQGISLayers()

    def updateActions(self):

        from qgis.utils import iface
        if isinstance(iface, QgisInterface):
            model = iface.layerTreeView().layerTreeModel()
            b = any(model.rootGroup().findLayerIds())
            self.actionSyncWithQGIS.setEnabled(b)

    def initActions(self):

        self.btnAddSource.setDefaultAction(self.actionAddDataSource)
        self.btnSync.setDefaultAction(self.actionSyncWithQGIS)
        self.btnRemoveSource.setDefaultAction(self.actionRemoveDataSource)
        self.btnCollapse.clicked.connect(lambda: self.dataSourceManagerTreeView().expandSelectedNodes(False))
        self.btnExpand.clicked.connect(lambda: self.dataSourceManagerTreeView().expandSelectedNodes(True))

    def expandSelectedNodes(self, treeView, expand):
        assert isinstance(treeView, QTreeView)

        treeView.selectAll()
        indices = treeView.selectedIndexes()
        if len(indices) == 0:
            treeView.selectAll()
            indices += treeView.selectedIndexes()
            treeView.clearSelection()
        for idx in indices:
            treeView.setExpanded(idx, expand)

    def connectDataSourceManager(self, dataSourceManager: DataSourceManager):
        """
        Initializes the panel with a DataSourceManager
        :param dataSourceManager: DataSourceManager
        """
        assert isinstance(dataSourceManager, DataSourceManager)
        self.mDataSourceManager = dataSourceManager
        self.mDataSourceManagerProxyModel.setSourceModel(self.mDataSourceManager)
        self.mDataSourceManagerTreeView.setModel(self.mDataSourceManagerProxyModel)
        self.mDataSourceManagerTreeView.selectionModel().selectionChanged.connect(self.onSelectionChanged)

    def onSelectionChanged(self, selected, deselected):

        s = self.selectedDataSources()
        self.actionRemoveDataSource.setEnabled(len(s) > 0)

    def selectedDataSources(self) -> List[DataSource]:
        """
        :return: [list-of-selected-DataSources]
        """
        sources = set()

        for idx in self.dataSourceManagerTreeView().selectionModel().selectedIndexes():
            assert isinstance(idx, QModelIndex)
            node = idx.data(Qt.UserRole)
            if isinstance(node, DataSource):
                sources.add(node)
            elif isinstance(node, DataSourceSet):
                for s in node:
                    sources.add(s)
        return list(sources)

    def projectSettingsKey(self) -> str:
        return self.__class__.__name__

    def projectSettings(self) -> Dict:
        sources = [dataSource.source() for dataSource in self.mDataSourceManager.dataSources()]
        return {
            'sources': sources
        }

    def setProjectSettings(self, settings: Dict):
        self.mDataSourceManager.addDataSources(settings['sources'])


class DataSourceFactory(object):

    @staticmethod
    def create(source: Any,
               name: str = None,
               show_dialogs: bool = True,
               project: Optional[QgsProject] = None,
               parent: Optional[QWidget] = None) -> List[DataSource]:
        """
        Searches the input for DataSources
        """
        if project is None:
            project = QgsProject.instance()

        results = []
        if isinstance(source, list):
            for s in source:
                results.extend(DataSourceFactory.create(s, name=name, project=project))
        else:
            if isinstance(source, DataSource):
                return [source]

                s = ""
            dataItem: Optional[QgsDataItem] = None
            if isinstance(source, QgsProviderSublayerDetails):
                source = source.toMimeUri()

            if isinstance(source, QgsMimeDataUtils.Uri):
                if source.layerType == 'raster':
                    dtype = QgsLayerItem.Raster
                    dataItem = LayerItem(None, source.name, source.uri, source.uri, dtype, source.providerKey)

                elif source.layerType == 'vector':
                    dtype = QgsLayerItem.Vector
                    dataItem = LayerItem(None, source.name, source.uri, source.uri, dtype, source.providerKey)

                elif source.providerKey in ['special:file', 'special:pkl']:
                    name = source.name
                    source = source.uri

                elif source.isValid():
                    source = source.uri
                    name = source.name

                else:
                    return []

            elif isinstance(source, QgsMapLayer):
                dtype = QgsLayerItem.typeFromMapLayer(source)
                dataItem = LayerItem(None, source.name(), source.source(), source.source(), dtype,
                                     source.providerType())
                dataItem.setIcon(QgsIconUtils.iconForLayer(source))

            if dataItem is None:
                if isinstance(source, Path):
                    source = source.as_posix()
                elif isinstance(source, QUrl):
                    source = source.toString(QUrl.PreferLocalFile | QUrl.RemoveQuery)

                if isinstance(source, str):
                    # try to find a source as layer in the current project
                    lyr = project.mapLayers().get(source, None)
                    if lyr is None:
                        # backup. try to find a source as layer in a global / standard project
                        lyr = QgsProject.instance().mapLayers().get(source, None)

                    if isinstance(lyr, QgsMapLayer):
                        return DataSourceFactory.create(lyr)

                    source = Path(source).as_posix()

                    if name is None:
                        name = Path(source).name

                    if re.search(r'\.(pkl)$', source, re.I):
                        dataItem = QgsDataItem(Qgis.BrowserItemType.Custom, None, name, source, 'special:pkl')
                    else:
                        providers = ['gdal', 'ogr']
                        providers = QgsProviderRegistry.instance().providerList()
                        sDetails = subLayerDetails(source, providers=providers)
                        if len(sDetails) == 1:
                            return DataSourceFactory.create(sDetails[0])
                        elif len(sDetails) > 1:
                            if show_dialogs:
                                # show sublayer selection dialog
                                d = SubDatasetSelectionDialog()
                                d.setWindowTitle('Select Layers')
                                from enmapbox import icon as enmapBoxIcon
                                d.setWindowIcon(enmapBoxIcon())
                                d.showMultiFiles(False)
                                d.setSubDatasetDetails(sDetails)
                                if d.exec_() == QDialog.Accepted:
                                    return DataSourceFactory.create(d.selectedSublayerDetails())
                                else:
                                    return []
                            else:
                                # create a data source for each sublayer
                                results = []
                                for d in sDetails:
                                    results.extend(DataSourceFactory.create(d))
                                return results

                    if dataItem is None:
                        if Path(source).is_file():
                            dataItem = QgsDataItem(Qgis.BrowserItemType.Custom, None, name, source, 'special:file')

            if isinstance(dataItem, QgsDataItem):
                ds: Optional[DataSource] = None
                if isinstance(dataItem, LayerItem):
                    if dataItem.providerKey() in ['memory']:
                        # get a reference to the layer
                        if isinstance(source, QgsVectorLayer):
                            if source.id() not in project.mapLayers():
                                project.addMapLayer(source, False)
                            dataItem.setReferenceLayer(source, project)
                        elif isinstance(source, QgsMimeDataUtils.Uri):
                            rx_uid = re.compile(r'uid={(?P<uid>[^}].*)}')
                            if match := rx_uid.match(source.data()):
                                layer_id = match.group('uid')
                                for p in [project, QgsProject.instance()]:
                                    p: QgsProject
                                    if layer_id in p.mapLayers():
                                        dataItem.setReferenceLayer(p.mapLayer(layer_id))
                                        break

                    if dataItem.mapLayerType() == QgsMapLayer.RasterLayer:
                        ds = RasterDataSource(dataItem)
                    elif dataItem.mapLayerType() == QgsMapLayer.VectorLayer:
                        ds = VectorDataSource(dataItem)
                elif dataItem.providerKey() == 'special:pkl':
                    ds = ModelDataSource(dataItem)
                elif dataItem.providerKey() == 'special:file':
                    ds = FileDataSource(dataItem)

                if isinstance(ds, DataSource):
                    results.append(ds)

        return results

    @staticmethod
    def srcToString(src) -> str:
        """
        Extracts the source uri that can be used to open a new QgsMapLayer
        :param src: QUrl | str
        :return: str
        """
        if isinstance(src, QUrl):
            src = src.toString(QUrl.PreferLocalFile | QUrl.RemoveQuery)
        if isinstance(src, str):
            # identify GDAL subdataset strings
            if re.search('(HDF|SENTINEL).*:.*:.*', src):
                src = src
            elif os.path.isfile(src):
                src = Path(src).as_posix()
            else:
                pass
        else:
            src = None
        return src
