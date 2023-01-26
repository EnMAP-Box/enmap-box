# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    dockmanager.py
    ---------------------
    Date                 : August 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import os
import re
import time
import typing
import uuid
from typing import Optional, List, Dict

from enmapbox import debugLog, messageLog
from enmapbox.gui import \
    SpectralLibrary, SpectralLibraryWidget, SpatialExtent, showLayerPropertiesDialog
from enmapbox.gui.datasources.datasources import DataSource, ModelDataSource
from enmapbox.gui.datasources.manager import DataSourceManager
from enmapbox.gui.dataviews.docks import Dock, DockArea, \
    AttributeTableDock, SpectralLibraryDock, TextDock, MimeDataDock, WebViewDock, LUT_DOCKTYPES, MapDock
from enmapbox.gui.mapcanvas import \
    MapCanvas, KEY_LAST_CLICKED
from enmapbox.gui.mimedata import \
    MDF_QGIS_LAYERTREEMODELDATA, MDF_ENMAPBOX_LAYERTREEMODELDATA, QGIS_URILIST_MIMETYPE, \
    MDF_TEXT_HTML, MDF_URILIST, MDF_TEXT_PLAIN, MDF_QGIS_LAYER_STYLE, \
    extractMapLayers, containsMapLayers
from enmapbox.gui.utils import enmapboxUiPath
from enmapbox.qgispluginsupport.qps.layerproperties import pasteStyleFromClipboard, pasteStyleToClipboard
from enmapbox.qgispluginsupport.qps.speclib.core import is_spectral_library, profile_field_list
from enmapbox.qgispluginsupport.qps.utils import loadUi, findParent
from qgis.PyQt.QtCore import Qt, QMimeData, QModelIndex, QObject, QTimer, pyqtSignal, QEvent, \
    QSortFilterProxyModel, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QDragEnterEvent, QDragMoveEvent, QDropEvent, QDragLeaveEvent
from qgis.PyQt.QtWidgets import QHeaderView, QMenu, QAbstractItemView, QApplication, QWidget, QToolButton, QAction
from qgis.PyQt.QtXml import QDomDocument, QDomElement
from qgis.core import Qgis, QgsMessageLog, QgsCoordinateReferenceSystem, QgsMapLayer, QgsVectorLayer, QgsRasterLayer, \
    QgsProject, QgsReadWriteContext, \
    QgsLayerTreeLayer, QgsLayerTreeNode, QgsLayerTreeGroup, \
    QgsLayerTreeModelLegendNode, QgsLayerTree, QgsLayerTreeModel, QgsLayerTreeUtils, \
    QgsPalettedRasterRenderer
from qgis.core import QgsWkbTypes
from qgis.gui import QgsLayerTreeProxyModel
from qgis.gui import QgsLayerTreeView, \
    QgsMapCanvas, QgsLayerTreeViewMenuProvider, QgsLayerTreeMapCanvasBridge, QgsDockWidget, QgsMessageBar
from typeguard import typechecked


class LayerTreeNode(QgsLayerTree):
    sigIconChanged = pyqtSignal()
    sigValueChanged = pyqtSignal(QObject)
    sigRemoveMe = pyqtSignal()

    def __init__(self, name: str, value=None, checked=Qt.Unchecked, tooltip=None, icon=None):
        # QObject.__init__(self)
        super(LayerTreeNode, self).__init__()
        # assert name is not None and len(str(name)) > 0

        self.mParent = None
        self.mTooltip: str = None
        self.mValue = None
        self.mIcon: QIcon = None

        self.mXmlTag = 'tree-node'

        self.setName(name)
        self.setValue(value)
        self.setExpanded(False)
        # self.setVisible(False)
        self.setTooltip(tooltip)
        self.setIcon(icon)

        # if parent is not None:
        #    parent.addChildNode(self)
        #    if isinstance(parent, LayerTreeNode):
        #        self.sigValueChanged.connect(parent.sigValueChanged)

    def dump(self, *args, **kwargs) -> str:

        d = super(LayerTreeNode, self).dump()
        d += '{}:"{}":"{}"\n'.format(self.__class__.__name__, self.name(), self.value())
        return d

    def xmlTag(self) -> str:
        return self.mXmlTag

    def _removeSubNode(self, node):
        if node in self.children():
            self.takeChild(node)
        return None

    def fetchCount(self):
        return 0

    def fetchNext(self):
        pass

    def setValue(self, value):
        self.mValue = value
        self.sigValueChanged.emit(self)

    def value(self):
        return self.mValue

    # def removeChildren(self, i0, cnt):
    #    self.removeChildrenPrivate(i0, cnt)
    #    self.updateVisibilityFromChildren()

    def setTooltip(self, tooltip):
        self.mTooltip = tooltip

    def tooltip(self, default=''):
        return self.mTooltip

    def setIcon(self, icon):
        if icon:
            assert isinstance(icon, QIcon)
        self.mIcon = icon
        self.sigIconChanged.emit()

    def icon(self):
        return self.mIcon

    def populateContextMenu(self, menu: QMenu):
        """
        Allows adding QActions and QMenu's to a parent menu
        """
        pass

    @staticmethod
    def readXml(element):

        raise NotImplementedError()

        return None

    @staticmethod
    def attachCommonPropertiesFromXML(node, element):
        assert 'tree-node' in element.tagName()

        node.setName(element.attribute('name'))
        node.setExpanded(element.attribute('expanded') == '1')
        node.setVisible(QgsLayerTreeUtils.checkStateFromXml(element.attribute("checked")))
        node.readCommonXml(element)

    def writeXML(self, parentElement):

        assert isinstance(parentElement, QDomElement)
        doc = parentElement.ownerDocument()
        elem = doc.createElement('tree-node')

        elem.setAttribute('name', self.name())
        elem.setAttribute('expanded', '1' if self.isExpanded() else '0')
        elem.setAttribute('checked', QgsLayerTreeUtils.checkStateToXml(Qt.Checked))

        # custom properties
        self.writeCommonXml(elem)

        for node in self.children():
            node.writeXML(elem)
        parentElement.appendChild(elem)

    def dropMimeData(self):
        raise NotImplementedError()

    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        return hash(id(self))


class DockTreeNode(LayerTreeNode):
    """
    Base TreeNode to symbolise a Dock
    """
    sigDockUpdated = pyqtSignal()

    def __init__(self, dock: Dock):
        assert isinstance(dock, Dock)
        self.dock = dock
        super(DockTreeNode, self).__init__('<dockname not available>')

        self.mIcon = QIcon(':/enmapbox/gui/ui/icons/viewlist_dock.svg')
        self.dock = dock
        self.setName(dock.title())
        self.dock.sigTitleChanged.connect(self.setName)
        self.mEnMAPBoxInstance = None

    def __repr__(self):
        return f'<{self.__class__.__name__} at {id(self)}>'

    def setEnMAPBoxInstance(self, enmapbox):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        if isinstance(enmapbox, EnMAPBox):
            self.mEnMAPBoxInstance = enmapbox

    def enmapBoxInstance(self) -> Optional['EnMAPBox']:  # noqa: F821
        return self.mEnMAPBoxInstance

    def writeXML(self, parentElement):
        elem = super(DockTreeNode, self).writeXML(parentElement)
        elem.setTagName('dock-tree-node')
        return elem

    def writeLayerTreeGroupXML(self, parentElement):
        QgsLayerTreeGroup.writeXML(self, parentElement)

        # return super(QgsLayerTreeNode,self).writeXml(parentElement)

    def mapLayers(self) -> List[QgsMapLayer]:
        """
        Returns the map layer related to this dock
        """
        raise NotImplementedError()


class TextDockTreeNode(DockTreeNode):
    def __init__(self, dock):
        assert isinstance(dock, TextDock)
        super(TextDockTreeNode, self).__init__(dock)
        self.setIcon(QIcon(':/enmapbox/gui/ui/icons/viewlist_dock.svg'))

        assert isinstance(dock, TextDock)

        self.fileNode = LayerTreeNode('File')
        dock.mTextDockWidget.sigSourceChanged.connect(self.setLinkedFile)
        self.setLinkedFile(dock.mTextDockWidget.mFile)
        self.addChildNode(self.fileNode)

    def setLinkedFile(self, path: str):
        self.fileNode.setName(f'File: {path}')
        self.fileNode.setValue(path)
        self.fileNode.setTooltip(path)


class AttributeTableDockTreeNode(DockTreeNode):
    def __init__(self, dock):
        assert isinstance(dock, AttributeTableDock)
        super(AttributeTableDockTreeNode, self).__init__(dock)
        self.setIcon(QIcon(r':/enmapbox/gui/ui/icons/viewlist_attributetabledock.svg'))


class SpeclibDockTreeNode(DockTreeNode):
    def __init__(self, dock):
        super().__init__(dock)

        self.setIcon(QIcon(':/enmapbox/gui/ui/icons/viewlist_spectrumdock.svg'))
        self.mSpeclibWidget: SpectralLibraryWidget = None
        self.profilesNode: LayerTreeNode = LayerTreeNode('Profiles')
        self.profilesNode.setIcon(QIcon(':/qps/ui/icons/profile.svg'))

        self.mPROFILES: typing.Dict[str, int] = dict()

        assert isinstance(dock, SpectralLibraryDock)
        self.mSpeclibWidget = dock.mSpeclibWidget
        assert isinstance(self.mSpeclibWidget, SpectralLibraryWidget)

        self.speclibNode = QgsLayerTreeLayer(self.speclib())

        # self.addChildNode(self.profilesNode)
        self.addChildNode(self.speclibNode)
        speclib = self.speclib()
        if is_spectral_library(speclib):
            speclib: QgsVectorLayer
            speclib.editCommandEnded.connect(self.updateNodes)
            speclib.committedFeaturesAdded.connect(self.updateNodes)
            speclib.committedFeaturesRemoved.connect(self.updateNodes)
            self.updateNodes()

    def speclib(self) -> SpectralLibrary:
        return self.speclibWidget().speclib()

    def speclibWidget(self) -> SpectralLibraryWidget:
        return self.mSpeclibWidget

    def updateNodes(self):

        PROFILES = dict()
        debugLog('update speclib nodes')
        if isinstance(self.mSpeclibWidget, SpectralLibraryWidget):
            sl: SpectralLibrary = self.mSpeclibWidget.speclib()
            if is_spectral_library(sl):
                # count number of profiles
                n = 0
                for field in profile_field_list(sl):
                    for f in sl.getFeatures(f'"{field.name()}" is not NULL'):
                        # show committed only?
                        # if f.id() >= 0:
                        n += 1
                    PROFILES[field.name()] = n

        if PROFILES != self.mPROFILES:
            self.profilesNode.removeAllChildren()
            new_nodes = []
            n_total = 0
            tt = [f'{len(PROFILES)} Spectral Profiles fields with:']
            for name, cnt in PROFILES.items():
                n_total += cnt
                node = LayerTreeNode(f'{name} {cnt}')
                node.setIcon(QIcon(r':/qps/ui/icons/profile.svg'))
                # node.setValue(cnt)
                tt.append(f'{name}: {cnt} profiles')
                new_nodes.append(node)
                self.profilesNode.addChildNode(node)

            self.profilesNode.setTooltip('\n'.join(tt))
            self.profilesNode.setName(f'{n_total} Profiles')
            self.profilesNode.setValue(n_total)

            self.mPROFILES = PROFILES


class MapDockTreeNode(DockTreeNode):
    """
    A TreeNode linked to a MapDock
    Acts like the QgsLayerTreeMapCanvasBridge
    """

    sigAddedLayers = pyqtSignal(list)
    sigRemovedLayers = pyqtSignal(list)

    def __init__(self, dock):
        super(MapDockTreeNode, self).__init__(dock)
        assert isinstance(self.dock, MapDock)

        # keep a reference on each map layer that is connected to a layer tree node
        self.mLayers: List[QgsMapLayer] = []
        self.mPreviousLayers: List[QgsMapLayer] = []

        self.setIcon(QIcon(':/enmapbox/gui/ui/icons/viewlist_mapdock.svg'))
        self.addedChildren.connect(self.onAddedChildren)
        self.removedChildren.connect(self.onRemovedChildren)

        canvas = self.dock.mapCanvas()
        assert isinstance(canvas, MapCanvas)
        self.mTreeCanvasBridge = MapCanvasBridge(self, canvas)
        # self.mTreeCanvasBridge = QgsLayerTreeMapCanvasBridge(self, canvas)
        canvas.setCanvasBridge(self.mTreeCanvasBridge)
        self.sigAddedLayers.connect(dock.sigLayersAdded.emit)
        self.sigRemovedLayers.connect(dock.sigLayersRemoved.emit)

    def onAddedChildren(self, node, idxFrom, idxTo):
        layers: List[QgsMapLayer] = self.mLayers[:]
        self.updateCanvas()
        added = [lyr for lyr in self.mLayers if lyr not in layers]
        if len(added) > 0:
            self.sigAddedLayers.emit(added)

    def onRemovedChildren(self, node, idxFrom, idxTo):
        layers = self.mLayers[:]
        self.updateCanvas()
        removed = [lyr for lyr in layers if lyr not in self.mLayers]
        if len(removed) > 0:
            self.sigRemovedLayers[list].emit(removed)

    def mapCanvas(self) -> MapCanvas:
        """
        Returns the MapCanvas
        :return: MapCanvas
        """
        return self.dock.mapCanvas()

    def updateCanvas(self):
        # save a reference on each layer in the tree
        self.mPreviousLayers = self.mLayers[:]
        self.mLayers = [n.layer() for n in self.findLayers() if isinstance(n.layer(), QgsMapLayer)]

        # ensure that layers have a project
        unregistered = [lyr for lyr in self.mLayers if not isinstance(lyr.project(), QgsProject)]
        if self.mapCanvas() is None:
            s = ""
        if self.mapCanvas().project() is None:
            s = ""
        project = self.mapCanvas().project()
        if len(unregistered) > 0 and isinstance(project, QgsProject):
            project.addMapLayers(unregistered, False)

        self.mTreeCanvasBridge.setCanvasLayers()

    @staticmethod
    def visibleLayers(node):
        """
        Returns the QgsMapLayers from all sub-nodes the are set as 'visible'
        :param node:
        :return:
        """
        lyrs = []
        if isinstance(node, list):
            for child in node:
                lyrs.extend(MapDockTreeNode.visibleLayers(child))

        elif isinstance(node, QgsLayerTreeGroup):
            for child in node.children():
                lyrs.extend(MapDockTreeNode.visibleLayers(child))

        elif isinstance(node, QgsLayerTreeLayer):
            if node.isVisible() == Qt.Checked:
                lyr = node.layer()
                if isinstance(lyr, QgsMapLayer):
                    lyrs.append(lyr)
                else:
                    s = ""  # logger.warning('QgsLayerTreeLayer.layer() is none')
        else:
            raise NotImplementedError()

        for lyr in lyrs:
            assert isinstance(lyr, QgsMapLayer), lyr

        return lyrs

    def removeLayerNodesByURI(self, uri: str):
        """
        Removes each layer node that relates to a source with the given uri
        :param uri:
        :type uri:
        :return:
        :rtype:
        """

        nodesToRemove = []
        for lyrNode in self.findLayers():
            lyr = lyrNode.layer()
            if isinstance(lyr, QgsMapLayer):
                uriLyr = lyrNode.layer().source()
                if uriLyr == uri:
                    nodesToRemove.append(lyrNode)

        for node in nodesToRemove:
            node.parent().takeChild(node)

    def addLayers(self, layers: List[QgsMapLayer]) -> List[QgsLayerTreeLayer]:

        return [self.addLayer(lyr) for lyr in layers]

    def insertLayer(self, idx, layerSource):
        """
        Inserts a new QgsMapLayer or SpatialDataSource on position idx by creating a new QgsMayTreeLayer node
        :param idx:
        :param layerSource:
        :return:
        """
        from enmapbox.gui.enmapboxgui import EnMAPBox

        mapLayers = []
        if isinstance(layerSource, QgsMapLayer):
            mapLayers.append(layerSource)
        else:
            s = ""
        emb = self.enmapBoxInstance()
        if isinstance(emb, EnMAPBox):
            emb.addSources(mapLayers)

        nodes = []
        for mapLayer in mapLayers:
            assert isinstance(mapLayer, QgsMapLayer)
            # QgsProject.instance().addMapLayer(mapLayer)
            nodes.append(QgsLayerTreeLayer(mapLayer))
            # self.layerNode.insertChildNode(idx, l)
        self.insertChildNodes(idx, nodes)


class DockManager(QObject):
    """
    Class to handle all DOCK related events
    """

    sigDockAdded = pyqtSignal(Dock)
    sigDockRemoved = pyqtSignal(Dock)
    sigDockWillBeRemoved = pyqtSignal(Dock)
    sigDockTitleChanged = pyqtSignal(Dock)

    def __init__(self):
        QObject.__init__(self)
        self.mConnectedDockAreas = []
        self.mCurrentDockArea = None
        self.mDocks = list()
        self.mDataSourceManager: Optional[DataSourceManager] = None
        self.mMessageBar: QgsMessageBar = Optional[None]
        self.mProject: QgsProject = QgsProject.instance()
        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.mEnMAPBoxInstance: Optional[EnMAPBox] = None

    def clear(self):
        """
        Removes all docks
        :return:
        """
        docks = self.docks()
        for dock in docks:
            self.removeDock(dock)

    def project(self) -> QgsProject:
        return self.mProject

    def setEnMAPBoxInstance(self, enmapBox):
        self.mEnMAPBoxInstance = enmapBox
        self.mEnMAPBoxInstance.project().layersWillBeRemoved.connect(self.onLayersWillBeRemoved)
        self.mProject = self.mEnMAPBoxInstance.project()

    def enmapBoxInstance(self) -> Optional['EnMAPBox']:  # noqa: F821
        return self.mEnMAPBoxInstance

    def setMessageBar(self, messageBar: QgsMessageBar):
        self.mMessageBar = messageBar

    def connectDataSourceManager(self, dataSourceManager: DataSourceManager):
        assert isinstance(dataSourceManager, DataSourceManager)
        self.mDataSourceManager = dataSourceManager
        self.setEnMAPBoxInstance(self.mDataSourceManager.enmapBoxInstance())

    def dataSourceManager(self) -> DataSourceManager:
        return self.mDataSourceManager

    def mapDocks(self) -> List[MapDock]:
        return [d for d in self if isinstance(d, MapDock)]

    def spectraLibraryDocks(self) -> List[SpectralLibraryDock]:
        return [d for d in self if isinstance(d, SpectralLibraryDock)]

    def connectDockArea(self, dockArea: DockArea):
        assert isinstance(dockArea, DockArea)

        dockArea.sigDragEnterEvent.connect(lambda event: self.onDockAreaDragDropEvent(dockArea, event))
        dockArea.sigDragMoveEvent.connect(lambda event: self.onDockAreaDragDropEvent(dockArea, event))
        dockArea.sigDragLeaveEvent.connect(lambda event: self.onDockAreaDragDropEvent(dockArea, event))
        dockArea.sigDropEvent.connect(lambda event: self.onDockAreaDragDropEvent(dockArea, event))
        self.mConnectedDockAreas.append(dockArea)

    def currentDockArea(self):
        if self.mCurrentDockArea not in self.mConnectedDockAreas and len(self.mConnectedDockAreas) > 0:
            self.mCurrentDockArea = self.mConnectedDockAreas[0]
        return self.mCurrentDockArea

    def onDockAreaDragDropEvent(self, dockArea, event):

        assert isinstance(dockArea, DockArea)

        assert isinstance(event, QEvent)

        if isinstance(event, QDragEnterEvent):
            # check mime types we can handle
            mimeData = event.mimeData()
            assert isinstance(mimeData, QMimeData)
            if containsMapLayers(mimeData):
                event.setDropAction(Qt.CopyAction)
                event.accept()
                return

        elif isinstance(event, QDragMoveEvent):
            event.accept()
            return
        elif isinstance(event, QDragLeaveEvent):
            event.accept()
            return

        elif isinstance(event, QDropEvent):
            mimeData = event.mimeData()
            assert isinstance(mimeData, QMimeData)

            # speclibs = extractSpectralLibraries(mimeData)
            # speclibUris = [s.source() for s in speclibs]

            layers = extractMapLayers(mimeData, project=self.project())
            rxSupportedFiles = re.compile(r'(xml|html|txt|csv|log|md|rst|qml)$')
            textfiles = []
            if len(layers) == 0:
                for url in mimeData.urls():
                    path = url.toLocalFile()
                    if os.path.isfile(path) and rxSupportedFiles.search(path):
                        textfiles.append(path)

            # register datasources

            new_sources = self.mDataSourceManager.addDataSources(layers + textfiles)

            # dropped_speclibs = [s for s in new_sources if isinstance(s, VectorDataSource) and s.isSpectralLibrary()]
            # dropped_maplayers = [s for s in new_sources if isinstance(s, SpatialDataSource) and s not in dropped_speclibs]

            dropped_speclibs = [lyr for lyr in layers if is_spectral_library(lyr)]
            dropped_maplayers = [lyr for lyr in layers if isinstance(lyr, QgsMapLayer) and lyr.isValid()]

            # open spectral Library dock for new speclibs

            if len(dropped_speclibs) > 0:
                # show 1st speclib
                from enmapbox.gui.dataviews.docks import SpectralLibraryDock
                NEW_DOCK = self.createDock(SpectralLibraryDock, speclib=dropped_speclibs[0])
                assert isinstance(NEW_DOCK, SpectralLibraryDock)

            # open map dock for other map layers

            # exclude vector layers without geometry
            dropped_maplayers = [
                lyr for lyr in dropped_maplayers
                if not (isinstance(lyr, QgsVectorLayer)
                        and lyr.geometryType() in
                        [QgsWkbTypes.UnknownGeometry, QgsWkbTypes.NullGeometry])]

            if len(dropped_maplayers) > 0:
                from enmapbox.gui.dataviews.docks import MapDock
                NEW_DOCK = self.createDock(MapDock)
                assert isinstance(NEW_DOCK, MapDock)
                # layers = [s.asMapLayer() for s in dropped_maplayers]
                NEW_DOCK.addLayers(dropped_maplayers)

            event.accept()

    def __len__(self):
        """
        Returns the number of Docks.
        :return: int
        """
        return len(self.mDocks)

    def __iter__(self):
        """
        Iterator over all Docks.
        """
        return iter(self.mDocks)

    def docks(self, dockType=None) -> List[Dock]:
        """
        Returns the managed docks.
        :param dockType: type of Dock to be returned. Default = None to return all Docks
        :return: [list-of-Docks controlled by this DockManager]
        """
        if isinstance(dockType, str):
            dockType = LUT_DOCKTYPES[dockType]
        if dockType is None:
            return self.mDocks[:]
        else:
            # handle wrapper types, e.g. when calling .dock(MapDock)
            return [d for d in self.mDocks if dockType.__name__ == d.__class__.__name__]

    def getDockWithUUID(self, uuid_):
        if isinstance(uuid_, str):
            uuid_ = uuid.UUID(uuid_)
        assert isinstance(uuid_, uuid.UUID)
        for dock in list(self.mDocks):
            assert isinstance(dock, Dock)
            if dock.uuid == uuid_:
                return dock

        return None

    def removeDock(self, dock):
        """
        Removes a Dock instances
        :param dock:
        :return:
        """
        if dock in self.mDocks:
            self.sigDockWillBeRemoved.emit(dock)
            self.mDocks.remove(dock)
            self.sigDockRemoved.emit(dock)
            if dock.container():
                dock.close()
            return True
        return False

    def createDock(self, dockType, *args, cls=None, **kwds) -> Dock:
        """
        Creates and returns a new Dock
        :param cls:
        :param dockType: str or Dock class, e.g. 'MAP' or MapDock
        :param args:
        :param kwds:
        :return:
        """

        assert dockType in LUT_DOCKTYPES.keys(), f'Unknown dockType "{dockType}"\n' + \
                                                 'Choose from [{}]'.format(
                                                     ','.join(['"{}"'.format(k) for k in LUT_DOCKTYPES.keys()]))

        if cls is None:
            cls = LUT_DOCKTYPES[dockType]  # use one of the hard coded types

        # create the dock name
        existingDocks = self.docks(dockType)
        existingNames = [d.title() for d in existingDocks]
        n = len(existingDocks) + 1
        dockTypes = [MapDock, TextDock, MimeDataDock, WebViewDock, SpectralLibraryDock, AttributeTableDock]
        dockBaseNames = ['Map', 'Text', 'MimeData', 'HTML Viewer', 'SpectralLibrary', 'Attribute Table']
        baseName = 'Dock'
        if cls in dockTypes:
            baseName = dockBaseNames[dockTypes.index(cls)]
        name = kwds.get('name', None)
        if name is None:
            name = '{} #{}'.format(baseName, n)
            while name in existingNames:
                n += 1
                name = '{} #{}'.format(baseName, n)
            kwds['name'] = name

        dockArea = kwds.get('dockArea', self.currentDockArea())
        assert isinstance(dockArea, DockArea), 'DockManager not connected to any DockArea yet. \n' \
                                               'Add DockAreas with connectDockArea(self, dockArea)'
        kwds['area'] = dockArea
        # kwds['parent'] = dockArea
        dock = None
        if issubclass(cls, MapDock):  # allow subclasses
            dock = cls(*args, **kwds)
            if isinstance(self.mDataSourceManager, DataSourceManager):
                dock.sigLayersAdded.connect(self.mDataSourceManager.addDataSources)

            from enmapbox.gui.enmapboxgui import EnMAPBox
            if isinstance(self.mEnMAPBoxInstance, EnMAPBox):
                dock.sigRenderStateChanged.connect(self.mEnMAPBoxInstance.ui.mProgressBarRendering.toggleVisibility)
            dock.mapCanvas().enableMapTileRendering(True)
            dock.mapCanvas().setParallelRenderingEnabled(True)
            dock.mapCanvas().setPreviewJobsEnabled(True)
            dock.mapCanvas().setCachingEnabled(True)
            dock.mapCanvas().setMapUpdateInterval(250)

        elif cls == TextDock:  # todo: allow subclasses for other dock types as well
            dock = TextDock(*args, **kwds)

        elif cls == MimeDataDock:
            dock = MimeDataDock(*args, **kwds)

        elif cls == WebViewDock:
            dock = WebViewDock(*args, **kwds)

        elif cls == SpectralLibraryDock:
            speclib = kwds.get('speclib')
            if isinstance(speclib, QgsVectorLayer):
                kwds['name'] = speclib.name()
            dock = SpectralLibraryDock(*args, **kwds)
            dock.speclib().willBeDeleted.connect(lambda *args, d=dock: self.removeDock(d))
            if isinstance(self.mMessageBar, QgsMessageBar):
                dock.mSpeclibWidget.setMainMessageBar(self.mMessageBar)
            dock.speclibWidget().setProject(self.project())
            self.dataSourceManager().addDataSources(dock.speclib())

            if speclib is None:
                sl = dock.speclib()
                # speclib did not exists before and is an in-memory layer?
                # remove source after closing the dock
                if isinstance(sl, QgsVectorLayer) and sl.providerType() == 'memory':
                    dock.sigClosed.connect(lambda *args, slib=sl: self.dataSourceManager().removeDataSources([sl]))

        elif cls == AttributeTableDock:
            layer = kwds.pop('layer', None)
            assert isinstance(layer, QgsVectorLayer), 'QgsVectorLayer "layer" is not defined'
            dock = AttributeTableDock(layer, *args, **kwds)
            layer.willBeDeleted.connect(lambda *args, d=dock: self.removeDock(d))
            if isinstance(self.mMessageBar, QgsMessageBar):
                dock.attributeTableWidget.setMainMessageBar(self.mMessageBar)
        else:
            raise Exception('Unknown dock type: {}'.format(dockType))
        # dock.setParent(dockArea)
        dockArea.addDock(dock, *args, **kwds)
        dock.setVisible(True)

        if dock not in self.mDocks:
            dock.sigClosed.connect(self.removeDock)
            self.mDocks.append(dock)
            self.sigDockAdded.emit(dock)

        return dock

    def onLayersWillBeRemoved(self, layer_ids: List[str]):

        to_remove = list()
        for dock in self.spectraLibraryDocks():
            dock: SpectralLibraryDock
            if dock.speclib().id() in layer_ids:
                to_remove.append(dock)
        for dock in to_remove:
            self.removeDock(dock)


class DockManagerTreeModel(QgsLayerTreeModel):
    def __init__(self, dockManager, parent=None):
        self.rootNode: LayerTreeNode = LayerTreeNode('<hidden root node>')
        assert isinstance(dockManager, DockManager)
        super(DockManagerTreeModel, self).__init__(self.rootNode, parent)
        self.columnNames = ['Property', 'Value']
        self.mProject: QgsProject = QgsProject.instance()

        if True:
            """
             // display flags
              ShowLegend                 = 0x0001,  //!< Add legend nodes for layer nodes
              ShowRasterPreviewIcon      = 0x0002,  //!< Will use real preview of raster layer as icon (may be slow)
              ShowLegendAsTree           = 0x0004,  //!< For legends that support it, will show them in a tree instead of a list (needs also ShowLegend). Added in 2.8
              DeferredLegendInvalidation = 0x0008,  //!< Defer legend model invalidation
              UseEmbeddedWidgets         = 0x0010,  //!< Layer nodes may optionally include extra embedded widgets (if used in QgsLayerTreeView). Added in 2.16

              // behavioral flags
              AllowNodeReorder           = 0x1000,  //!< Allow reordering with drag'n'drop
              AllowNodeRename            = 0x2000,  //!< Allow renaming of groups and layers
              AllowNodeChangeVisibility  = 0x4000,  //!< Allow user to set node visibility with a check box
              AllowLegendChangeState     = 0x80
            """
            self.setFlag(QgsLayerTreeModel.ShowLegend, True)
            self.setFlag(QgsLayerTreeModel.ShowLegendAsTree, True)
            # self.setFlag(QgsLayerTreeModel.ShowRasterPreviewIcon, False)

            self.setFlag(QgsLayerTreeModel.DeferredLegendInvalidation, False)
            # self.setFlag(QgsLayerTreeModel.UseEmbeddedWidget, True)

            # behavioral
            self.setFlag(QgsLayerTreeModel.AllowNodeReorder, True)
            self.setFlag(QgsLayerTreeModel.AllowNodeRename, True)
            self.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility, True)
            self.setFlag(QgsLayerTreeModel.AllowLegendChangeState, True)
            # self.setFlag(QgsLayerTreeModel.ActionHierarchical, False)

            self.setAutoCollapseLegendNodes(10)

        self.mDockManager = dockManager

        for dock in dockManager:
            self.addDock(dock)

        self.mDockManager.sigDockAdded.connect(self.addDock)
        self.mDockManager.sigDockRemoved.connect(self.removeDock)

    def setProject(self, project: QgsProject):
        self.mProject = project

    def project(self) -> QgsProject:
        return self.mProject

    def findDockNode(self, object: typing.Union[str, QgsMapCanvas, QgsRasterLayer,
                                                QgsVectorLayer, SpectralLibraryWidget]) -> DockTreeNode:
        """
        Returns the dock that contains the given object
        :param object:
        :return:
        """
        if isinstance(object, MapCanvas):
            return self.mapDockTreeNode(object)
        elif isinstance(object, SpectralLibraryWidget):
            for node in self.dockTreeNodes():
                if isinstance(node, SpeclibDockTreeNode) and node.speclibWidget() == object:
                    return node
        elif isinstance(object, QgsMapLayer):
            for node in self.dockTreeNodes():
                if isinstance(node, MapDockTreeNode) and node.findLayer(object):
                    return node

        else:
            node = self.rootNode.findGroup(str(object))
            if isinstance(node, DockTreeNode):
                return node
        return None

    def columnCount(self, index) -> int:
        node = self.index2node(index)
        return 1
        #  if type(node) in [DockTreeNode, QgsLayerTreeGroup, QgsLayerTreeLayer]:
        #      return 1
        #  elif isinstance(node, LayerTreeNode):
        #      return 2
        #  else:
        #      return 1

    def supportedDragActions(self):
        """
        """
        return Qt.CopyAction | Qt.MoveAction

    def supportedDropActions(self) -> Qt.DropActions:
        """
        """
        return Qt.CopyAction | Qt.MoveAction

    def addDock(self, dock: Dock) -> DockTreeNode:
        """
        Adds a Dock and returns the DockTreeNode
        :param dock:
        :return:
        """
        dockNode = createDockTreeNode(dock)
        dockNode.setEnMAPBoxInstance(self.mDockManager.enmapBoxInstance())

        if isinstance(dockNode, DockTreeNode):
            self.rootNode.addChildNode(dockNode)
            if self.rowCount() == 1:
                # fix for
                # https://bitbucket.org/hu-geomatics/enmap-box/issues/361/newly-created-mapview-is-not-checked-as
                QTimer.singleShot(500, self.update_docknode_visibility)
                pass
        return dock

    def update_docknode_visibility(self):

        QApplication.processEvents()

        if self.rowCount() > 0:
            idx0 = self.index(0, 0)
            idx1 = self.index(self.rowCount() - 1, 0)
            self.dataChanged.emit(idx0, idx1, [Qt.CheckStateRole])

    def canFetchMore(self, index) -> bool:
        node = self.index2node(index)
        if isinstance(node, LayerTreeNode):
            return len(node.children()) < node.fetchCount()
        return False

    def removeDock(self, dock):
        rootNode = self.rootNode
        to_remove = [n for n in rootNode.children() if n.dock == dock]
        keep_ref = [n.layer() for n in rootNode.findLayers()]
        self.removeNodes(to_remove)
        keep_ref.clear()

    def removeDataSources(self, dataSources: List[DataSource]):
        """
        Removes nodes that relate to a specific DataSource
        :param dataSource:
        :type dataSource:
        :return:
        :rtype:
        """
        if not isinstance(dataSources, list):
            dataSources = list(dataSources)

        docks_to_close = []
        for d in dataSources:
            assert isinstance(d, DataSource)

            for node in self.rootNode.children():
                if isinstance(node, MapDockTreeNode):
                    # remove layers from map canvas
                    node.removeLayerNodesByURI(d.source())
                else:
                    # close docks linked to this source
                    if isinstance(node, AttributeTableDockTreeNode) \
                            and isinstance(node.dock, AttributeTableDock) \
                            and isinstance(node.dock.vectorLayer(), QgsVectorLayer) \
                            and node.dock.vectorLayer().source() == d.source():
                        docks_to_close.append(node.dock)

                    elif isinstance(node, SpeclibDockTreeNode) \
                            and isinstance(node.speclib(), QgsVectorLayer) \
                            and node.speclib().source() == d.source():
                        docks_to_close.append(node.dock)

        for dock in docks_to_close:
            self.mDockManager.removeDock(dock)

    def dockManager(self) -> DockManager:
        return self.mDockManager

    def dockTreeNodes(self) -> List[DockTreeNode]:
        return [n for n in self.rootNode.children() if isinstance(n, DockTreeNode)]

    def mapDockTreeNodes(self) -> List[MapDockTreeNode]:
        """
        Returns all MapDockTreeNodes
        :return: [list-of-MapDockTreeNodes]
        """
        return [n for n in self.dockTreeNodes() if isinstance(n, MapDockTreeNode)]

    def mapDockTreeNode(self, canvas: QgsMapCanvas) -> MapDockTreeNode:
        """
        Returns the MapDockTreeNode that is connected to `canvas`
        :param canvas: QgsMapCanvas
        :type canvas:
        :return: MapDockTreeNode
        :rtype:
        """
        for n in self.mapDockTreeNodes():
            if n.mapCanvas() == canvas:
                return n
        return None

    def mapCanvases(self) -> List[MapCanvas]:
        """
        Returns all MapCanvases
        :return: [list-of-MapCanvases]
        """
        return [n.mapCanvas() for n in self.mapDockTreeNodes() if isinstance(n.mapCanvas(), MapCanvas)]

    def mapLayerIds(self) -> List[str]:
        ids = []
        for node in self.mapDockTreeNodes():
            if isinstance(node, MapDockTreeNode):
                ids.extend(node.findLayerIds())
        return ids

    def mapLayers(self) -> List[QgsMapLayer]:
        """
        Returns all map layers, also those that are invisible and not added to a QgsMapCanvas
        :return: [list-of-QgsMapLayer]
        """
        layers = []
        for node in self.rootGroup().findLayers():
            lyr = node.layer()
            if isinstance(lyr, QgsMapLayer) and lyr not in layers:
                layers.append(lyr)

        for dockNode in self.rootGroup().children():
            if isinstance(dockNode, SpeclibDockTreeNode):
                lyr = dockNode.speclib()
                if isinstance(lyr, QgsMapLayer) and lyr not in layers:
                    layers.append(lyr)

        return layers

    def removeLayers(self, layerIds: List[str]):
        """Removes the node linked to map layers"""
        assert isinstance(layerIds, list)

        mapDockTreeNodes = [n for n in self.rootNode.children() if isinstance(n, MapDockTreeNode)]
        to_remove = []
        for mapDockTreeNode in mapDockTreeNodes:
            assert isinstance(mapDockTreeNode, MapDockTreeNode)
            for lid in layerIds:
                node = mapDockTreeNode.findLayer(lid)
                if isinstance(node, QgsLayerTreeLayer):
                    to_remove.append(node)
        self.removeNodes(to_remove)

    def removeNodes(self, nodes: List[QgsLayerTreeNode]):
        for n in nodes:
            if isinstance(n, QgsLayerTreeNode) and isinstance(n.parent(), QgsLayerTreeNode):
                n.parent().takeChild(n)

    def removeDockNode(self, node):
        self.removeNodes([node])
        # self.mDockManager.removeDock(node.dock)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        node = self.index2node(index)
        if node is None:
            node = self.index2legendNode(index)
            if isinstance(node, QgsLayerTreeModelLegendNode):
                return self.legendNodeFlags(node)
                # return super(QgsLayerTreeModel,self).flags(index)
                # return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
            else:
                return Qt.NoItemFlags
        else:
            # print('node: {}  {}'.format(node, type(node)))
            dockNode = self.parentNodesFromIndices(index, nodeInstanceType=DockTreeNode)
            if len(dockNode) == 0:
                return Qt.NoItemFlags
            elif len(dockNode) > 1:
                # print('DEBUG: Multiple docknodes selected')
                return Qt.NoItemFlags
            else:
                dockNode = dockNode[0]

            column = index.column()
            isL1 = node.parent() == self.rootNode
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

            # normal tree nodes

            if isinstance(node, LayerTreeNode):
                if column == 0:

                    if isinstance(node, DockTreeNode):
                        flags = flags | Qt.ItemIsUserCheckable | \
                                Qt.ItemIsEditable | \
                                Qt.ItemIsDropEnabled

                        if isL1:
                            flags = flags | Qt.ItemIsDropEnabled

                    if node.name() == 'Layers':
                        flags = flags | Qt.ItemIsUserCheckable | Qt.ItemIsEditable

                    if isinstance(node, CheckableLayerTreeNode):
                        flags = flags | Qt.ItemIsUserCheckable

                if column == 1:
                    pass
                    # mapCanvas Layer Tree Nodes
            elif type(node) in [QgsLayerTreeLayer, QgsLayerTreeGroup]:
                if column == 0:
                    flags = flags | Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled

                # if isinstance(dockNode, MapDockTreeNode) and node != dockNode.layerNode:
                # if isinstance(dockNode, MapDockTreeNode) and node != dockNode.layerNode:
                #    flags = flags | Qt.ItemIsDragEnabled
            elif not isinstance(node, QgsLayerTree):
                s = ""
            else:
                s = ""

            if not isinstance(dockNode, MapDockTreeNode):
                flags = flags & ~Qt.ItemIsDragEnabled
            return flags

    def headerData(self, section, orientation, role=None):
        if role == Qt.DisplayRole:
            return self.columnNames[section]
        return None

    def mimeTypes(self):
        # specifies the mime types handled by this model
        types = [MDF_ENMAPBOX_LAYERTREEMODELDATA,
                 MDF_QGIS_LAYERTREEMODELDATA,
                 MDF_TEXT_HTML,
                 MDF_TEXT_PLAIN,
                 MDF_URILIST]
        return types

    def canDropMimeData(self, data, action, row, column, parent):
        if 'application/x-vnd.qgis.qgis.uri' in data.formats():
            return True
        else:
            return super().canDropMimeData(data, action, row, column, parent)

    def dropMimeData(self, mimeData, action, row, column, parentIndex):
        assert isinstance(mimeData, QMimeData)

        if not parentIndex.isValid():
            return False

        # layerRegistry = None
        # if isinstance(EnMAPBox.instance(), EnMAPBox):
        #    layerRegistry = EnMAPBox.instance().mapLayerStore()

        parentNode = self.index2node(parentIndex)
        # get parent DockNode
        dockNode = self.parentNodesFromIndices(parentIndex, nodeInstanceType=DockTreeNode)

        if len(dockNode) != 1:
            return False
        else:
            dockNode = dockNode[0]

        if isinstance(dockNode, MapDockTreeNode):

            parentLayerGroup = self.parentNodesFromIndices(parentIndex, nodeInstanceType=QgsLayerTreeGroup)
            if parentIndex.isValid() and row == -1:
                # if dropped onto group, insert at first position
                row = 0
            assert len(parentLayerGroup) == 1
            parentLayerGroup = parentLayerGroup[0]

            ok = False
            qgisPid = None
            if 'application/qgis.application.pid' in mimeData.formats():
                qgisPid, ok = mimeData.data('application/qgis.application.pid').toInt()

                if ok and qgisPid != QCoreApplication.applicationPid():
                    raise NotImplementedError()
                else:
                    encodedLayerTreeData = mimeData.data('application/qgis.layertreemodeldata')

                    layerTreeDoc = QDomDocument()
                    if not layerTreeDoc.setContent(encodedLayerTreeData):
                        return False
                    rootLayerTreeElem = layerTreeDoc.documentElement()
                    if rootLayerTreeElem.tagName() != 'layer_tree_model_data':
                        return False
                    nodes = []
                    elem: QDomElement = rootLayerTreeElem.firstChildElement()
                    while not elem.isNull():
                        node = QgsLayerTreeNode.readXml(elem, self.project())
                        if isinstance(node, QgsLayerTreeNode):
                            nodes.append(node)
                        elem = elem.nextSiblingElement()

                    if len(nodes) == 0:
                        return False
                    parentLayerGroup.insertChildNodes(row, nodes)
                return True
            else:
                # try other approaches that extract the layer instances
                mapLayers = extractMapLayers(mimeData, project=self.project())
                if action == Qt.CopyAction:
                    mapLayers = [lyr.clone() for lyr in mapLayers]

                i = row
                if len(mapLayers) > 0:
                    for lyr in mapLayers:
                        parentLayerGroup.insertLayer(i, lyr)
                        i += 1
                    return True

        elif isinstance(dockNode, TextDockTreeNode):
            s = ""

        return False

    def mimeData(self, indexes):
        indexes = sorted(indexes)

        if len(indexes) == 0:
            return None

        nodesFinal = self.indexes2nodes(indexes, True)

        mimeSuper = super(DockManagerTreeModel, self).mimeData(indexes)
        if True:
            return mimeSuper

        mimeData = QMimeData()
        doc = QDomDocument()
        rootElem = doc.createElement("dock_tree_model_data")
        context = QgsReadWriteContext()
        for node in nodesFinal:
            node.writeXml(rootElem, context)
        doc.appendChild(rootElem)
        mimeData.setData(MDF_ENMAPBOX_LAYERTREEMODELDATA, doc.toByteArray())

        if MDF_QGIS_LAYERTREEMODELDATA in mimeSuper.formats():
            mimeData.setData(MDF_ENMAPBOX_LAYERTREEMODELDATA, mimeSuper.data(MDF_QGIS_LAYERTREEMODELDATA))
            # mimeData.setData(MDF_LAYERTREEMODELDATA, mimeSuper.data(MDF_LAYERTREEMODELDATA))

        if QGIS_URILIST_MIMETYPE in mimeSuper.formats():
            mimeData.setData(QGIS_URILIST_MIMETYPE, mimeSuper.data(QGIS_URILIST_MIMETYPE))

        return mimeData

    def parentNodesFromIndices(self, indices, nodeInstanceType=DockTreeNode):
        """
        Returns all DockNodes contained or parent to the given indices
        :param indices:
        :return:
        """
        results = set()
        if type(indices) is QModelIndex:
            node = self.index2node(indices)
            while node is not None and not isinstance(node, nodeInstanceType):
                node = node.parent()
            if node is not None:
                results.add(node)
        else:
            for ind in indices:
                results.update(self.parentNodesFromIndices(ind, nodeInstanceType=nodeInstanceType))

        return list(results)

    def data(self, index, role):
        if not index.isValid():
            return None

        node = self.index2node(index)
        legendNode = self.index2legendNode(index)
        column = index.column()

        if isinstance(legendNode, QgsLayerTreeModelLegendNode):
            # print(('LEGEND', node, column, role))
            return super(DockManagerTreeModel, self).data(index, role)

        elif type(node) in [QgsLayerTreeLayer, QgsLayerTreeGroup, QgsLayerTree]:
            # print(('QGSNODE', node, column, role))
            if role == Qt.EditRole:
                s = ""

            if isinstance(node, QgsLayerTree) and column > 0:
                return None

            if column == 1:
                if role in [Qt.DisplayRole, Qt.EditRole]:
                    return node.name()

            return super(DockManagerTreeModel, self).data(index, role)
        elif isinstance(node, LayerTreeNode):

            if column == 0:

                if role in [Qt.DisplayRole, Qt.EditRole]:
                    return node.name()
                if role == Qt.DecorationRole:
                    return node.icon()
                if role == Qt.ToolTipRole:
                    return node.tooltip()
                if role == Qt.CheckStateRole:
                    if isinstance(node, DockTreeNode):
                        if isinstance(node.dock, Dock):
                            return Qt.Checked if node.dock.isVisible() else Qt.Unchecked
                    if isinstance(node, CheckableLayerTreeNode):
                        return node.checkState()
            elif column == 1:
                if role == Qt.DisplayRole:
                    # print(node.value())
                    return node.value()

                if role == Qt.EditRole:
                    return node.value()

            else:
                # if role == Qt.DisplayRole and isinstance(node, TreeNode):
                #    return node.value()
                return super(DockManagerTreeModel, self).data(index, role)

        return None

        # return super(DockManagerTreeModel, self).data(index, role)

    def setData(self, index, value, role=None):

        node = self.index2node(index)
        if node is None:
            node = self.index2legendNode(index)
            if isinstance(node, QgsLayerTreeModelLegendNode):
                # this does not work:
                # result = super(QgsLayerTreeModel,self).setData(index, value, role=role)
                if role == Qt.CheckStateRole and not self.testFlag(QgsLayerTreeModel.AllowLegendChangeState):
                    return False
                result = node.setData(value, role)
                if result:
                    self.dataChanged.emit(index, index)
                return result

        parentNode = node.parent()

        result = False
        if isinstance(node, DockTreeNode) and isinstance(node.dock, Dock):
            if role == Qt.CheckStateRole:
                if value == Qt.Unchecked:
                    node.dock.setVisible(False)
                else:
                    node.dock.setVisible(True)
                result = True
            if role == Qt.EditRole and len(value) > 0:
                node.dock.setTitle(value)
                result = True

        if isinstance(node, CheckableLayerTreeNode) and role == Qt.CheckStateRole:
            node.setCheckState(Qt.Unchecked if value in [False, 0, Qt.Unchecked] else Qt.Checked)
            return True

        if type(node) in [QgsLayerTreeLayer, QgsLayerTreeGroup]:

            if role == Qt.CheckStateRole:
                node.setItemVisibilityChecked(value)
                mapDockNode = node.parent()
                while mapDockNode is not None and not isinstance(mapDockNode, MapDockTreeNode):
                    mapDockNode = mapDockNode.parent()

                if isinstance(mapDockNode, MapDockTreeNode):
                    mapDockNode.updateCanvas()
                    result = True
            if role == Qt.EditRole:
                if isinstance(node, QgsLayerTreeLayer):
                    node.setName(value)
                    result = True
                if isinstance(node, QgsLayerTreeGroup):
                    node.setName(value)
                    result = True

        if result:
            self.dataChanged.emit(index, index)
        return result


class DockManagerTreeProxyModel(QSortFilterProxyModel):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)


class DockTreeView(QgsLayerTreeView):
    sigPopulateContextMenu = pyqtSignal(QMenu)

    def __init__(self, parent: QWidget = None):
        super(DockTreeView, self).__init__(parent)

        self.setHeaderHidden(False)
        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.currentLayerChanged.connect(self.onCurrentLayerChanged)
        self.setEditTriggers(QAbstractItemView.EditKeyPressed)

        self.mMenuProvider = DockManagerLayerTreeModelMenuProvider(self)
        self.setMenuProvider(self.mMenuProvider)

    def findParentMapDockTreeNode(self, node: QgsLayerTreeNode) -> MapDockTreeNode:
        while isinstance(node, QgsLayerTreeNode) and not isinstance(node, MapDockTreeNode):
            node = node.parent()
        if isinstance(node, MapDockTreeNode):
            return node
        else:
            return None

    def onCurrentLayerChanged(self, layer: QgsMapLayer):
        if not isinstance(layer, QgsMapLayer):
            return
        debugLog('DockTreeView:onCurrentLayerChanged')
        # find QgsLayerTreeNodes connects to this layer
        currentLayerNode = self.currentNode()
        if not (isinstance(currentLayerNode, QgsLayerTreeLayer) and currentLayerNode.layerId() == layer.id()):
            # find the QgsLayerTreeNode
            currentLayerNode = self.layerTreeModel().rootNode.findLayer(layer)

        map_node = self.findParentMapDockTreeNode(currentLayerNode)
        if isinstance(map_node, MapDockTreeNode):
            self.setCurrentMapCanvas(map_node.mapCanvas())

        for canvas in self.layerTreeModel().mapCanvases():
            assert isinstance(canvas, MapCanvas)
            if layer in canvas.layers():
                canvas.setCurrentLayer(layer)

        debugLog(f'DockTreeView current layer : {self.currentLayer()}')
        debugLog(f'DockTreeView current canvas: {self.currentMapCanvas()}')

    def selectedDockNodes(self) -> List[DockTreeNode]:

        nodes = []
        proxymodel = isinstance(self.model(), QSortFilterProxyModel)
        for idx in self.selectedIndexes():
            if proxymodel:
                node = self.layerTreeModel().index2node(self.model().mapToSource(idx))
            else:
                node = self.index2node(idx)

            if isinstance(node, DockTreeNode) and node not in nodes:
                nodes.append(node)
        return nodes

    def setCurrentMapCanvas(self, canvas: QgsMapCanvas):

        if canvas in self.mapCanvases():
            canvas.setProperty(KEY_LAST_CLICKED, time.time())
            return True
        else:
            return False

    def currentMapCanvas(self) -> Optional[MapCanvas]:
        """
        Returns the current MapCanvas, i.e. the MapCanvas that was clicked last
        :return:
        :rtype:
        """
        canvases = sorted(self.mapCanvases(), key=lambda c: c.property(KEY_LAST_CLICKED))
        if len(canvases) > 0:
            return canvases[-1]
        else:
            return None

    def mapCanvases(self) -> List[MapCanvas]:
        return self.layerTreeModel().mapCanvases()

    def setModel(self, model):
        assert isinstance(model, DockManagerTreeModel)

        super(DockTreeView, self).setModel(model)
        model.rootNode.addedChildren.connect(self.onNodeAddedChildren)
        for c in model.rootNode.findChildren(LayerTreeNode):
            self.setColumnSpan(c)

    def enmapBoxInstance(self):
        m = self.model()
        if isinstance(m, QSortFilterProxyModel):
            m = m.sourceModel()
        if isinstance(m, DockManagerTreeModel):
            return m.mDockManager.enmapBoxInstance()
        return None

    def layerTreeModel(self) -> DockManagerTreeModel:
        return super().layerTreeModel()

    def onNodeAddedChildren(self, parent, iFrom, iTo):
        for i in range(iFrom, iTo + 1):
            node = parent.children()[i]
            if isinstance(node, LayerTreeNode):
                node.sigValueChanged.connect(self.setColumnSpan)

            self.setColumnSpan(node)

        n_added = iTo - iFrom + 1
        if isinstance(parent, DockTreeNode) and len(parent.children()) == n_added:
            parent.setExpanded(True)

        # select added layer
        if self.state() == QAbstractItemView.NoState:
            for child in reversed(parent.children()):
                if isinstance(child, QgsLayerTreeLayer):
                    idx = self.node2index(child)
                    self.setCurrentIndex(idx)
                    break

    def setColumnSpan(self, node):
        parent = node.parent()
        if parent is not None:
            model = self.layerTreeModel()
            idxNode = model.node2index(node)
            idxParent = model.node2index(parent)
            span = False
            if isinstance(node, LayerTreeNode):
                span = node.value() is None or '{}'.format(node.value()).strip() == ''
            elif type(node) in [QgsLayerTreeGroup, QgsLayerTreeLayer]:
                span = True

            m = self.model()
            # account for changes model() return between 3.16 and 3.18
            if isinstance(m, QSortFilterProxyModel):
                idxNode = m.mapFromSource(idxNode)
                idxParent = m.mapFromSource(idxParent)

            self.setFirstColumnSpanned(idxNode.row(), idxParent, span)
            # for child in node.children():
            #    self.setColumnSpan(child)


class DockManagerLayerTreeModelMenuProvider(QgsLayerTreeViewMenuProvider):
    # class Signals(QObject):
    #    sigPopulateContextMenu = pyqtSignal(QMenu)
    #
    #    def __init__(self, *args, **kwds):
    #        super().__init__(*args, **kwds)

    def __init__(self, treeView: DockTreeView):
        super(DockManagerLayerTreeModelMenuProvider, self).__init__()
        # QObject.__init__(self)
        assert isinstance(treeView, DockTreeView)
        self.mDockTreeView: DockTreeView = treeView
        # self.mSignals = DockManagerLayerTreeModelMenuProvider.Signals()

    def enmapboxInstance(self):
        return self.mDockTreeView.enmapBoxInstance()

    def createContextMenu(self):

        cidx: QModelIndex = self.mDockTreeView.currentIndex()
        col = cidx.column()
        node = self.mDockTreeView.currentNode()
        if node is None or node == self.mDockTreeView.layerTreeModel().rootGroup():
            return

        viewNode = findParent(node, DockTreeNode, checkInstance=True)

        errors: List[ModuleNotFoundError] = []

        menu = QMenu()
        menu.setToolTipsVisible(True)

        lyr: QgsMapLayer = None
        canvas: QgsMapCanvas = None
        if isinstance(viewNode, MapDockTreeNode):
            assert isinstance(viewNode.dock, MapDock)
            canvas = viewNode.dock.mCanvas

        selectedLayerNodes = list(set(self.mDockTreeView.selectedLayerNodes()))

        if isinstance(node, (DockTreeNode, QgsLayerTreeLayer, QgsLayerTreeGroup)):
            actionEdit = menu.addAction('Rename')
            actionEdit.setShortcut(Qt.Key_F2)
            actionEdit.triggered.connect(lambda *args, idx=cidx: self.mDockTreeView.edit(idx))

        if isinstance(node, MapDockTreeNode) or isinstance(viewNode, MapDockTreeNode) \
                and isinstance(node, (QgsLayerTreeGroup, QgsLayerTreeLayer)):
            action = menu.addAction('Add Group')
            action.setIcon(QIcon(':/images/themes/default/mActionAddGroup.svg'))
            action.triggered.connect(self.onAddGroup)

        if type(node) is QgsLayerTreeGroup:
            action = menu.addAction('Remove Group')
            action.setToolTip('Remove the layer group')
            action.triggered.connect(
                lambda *arg, nodes=[node]: self.mDockTreeView.layerTreeModel().removeNodes(nodes))

        if type(node) is QgsLayerTreeLayer:
            # get parent dock node -> related map canvas
            lyr = node.layer()

            if isinstance(lyr, QgsMapLayer):
                try:
                    self.addMapLayerMenuItems(node, menu, canvas, selectedLayerNodes)
                except ModuleNotFoundError as ex:
                    errors.append(ex)

            if isinstance(lyr, QgsVectorLayer):
                try:
                    self.addVectorLayerMenuItems(node, menu)
                except ModuleNotFoundError as ex:
                    errors.append(ex)

            if isinstance(lyr, QgsRasterLayer):
                try:
                    self.addRasterLayerMenuItems(node, menu)
                except ModuleNotFoundError as ex:
                    errors.append(ex)

        elif isinstance(node, DockTreeNode):
            assert isinstance(node.dock, Dock)
            try:
                node.dock.populateContextMenu(menu)
            except ModuleNotFoundError as ex:
                errors.append(ex)

        elif isinstance(node, LayerTreeNode):
            if col == 0:
                try:
                    node.populateContextMenu(menu)
                except ModuleNotFoundError as ex:
                    errors.append(ex)
            elif col == 1:
                a = menu.addAction('Copy')
                a.triggered.connect(lambda *args, n=node: QApplication.clipboard().setText('{}'.format(n.value())))

        # last chance to add other menu actions
        # self.mSignals.sigPopulateContextMenu.emit(menu)
        if isinstance(self.mDockTreeView, DockTreeView):
            try:
                self.mDockTreeView.sigPopulateContextMenu.emit(menu)
            except ModuleNotFoundError as ex:
                errors.append(ex)

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

                messageLog(msg)
                QgsMessageLog.logMessage(msg, level=Qgis.MessageLevel.Warning)

        return menu

    def addMapLayerMenuItems(self, node: QgsLayerTreeLayer, menu: QMenu, canvas: QgsMapCanvas, selectedLayerNodes):
        """
        Add menu actions that handle QgsMapLayers in general
        :param lyr:
        :param menu:
        :return:
        """
        lyr = node.layer()
        if isinstance(canvas, QgsMapCanvas):
            action = menu.addAction('Zoom to layer')
            action.setIcon(QIcon(':/images/themes/default/mActionZoomToLayer.svg'))
            action.triggered.connect(lambda *args, _lyr=lyr, c=canvas: self.onZoomToLayer(_lyr, c))

            action = menu.addAction('Set layer CRS to map canvas')
            action.triggered.connect(lambda: canvas.setDestinationCrs(lyr.crs()))

            def onDuplicateLayer(n: QgsLayerTreeLayer):

                group = n.parent()
                if isinstance(group, QgsLayerTreeGroup):
                    lyrClone = n.layer().clone()
                    lyrClone.setName(f'{lyr.clone().name()} copy')
                    QgsLayerTreeUtils.insertLayerBelow(group, n.layer(), lyrClone)

            action = menu.addAction('Duplicate Layer')
            action.setIcon(QIcon(':/images/themes/default/mActionDuplicateLayer.svg'))
            action.triggered.connect(lambda *args, n=node: onDuplicateLayer(n))
            action.setEnabled(isinstance(lyr, QgsMapLayer))

            action = menu.addAction('Remove layer')
            action.setIcon(QIcon(':/images/themes/default/mActionRemoveLayer.svg'))
            action.setToolTip('Remove layer from map canvas')
            action.triggered.connect(
                lambda *arg, nodes=selectedLayerNodes: self.mDockTreeView.layerTreeModel().removeNodes(nodes))

        actionPasteStyle = menu.addAction('Paste Style')
        actionPasteStyle.triggered.connect(lambda *args, _lyr=lyr: pasteStyleFromClipboard(_lyr))
        actionPasteStyle.setEnabled(MDF_QGIS_LAYER_STYLE in QApplication.clipboard().mimeData().formats())
        actionCopyStyle = menu.addAction('Copy Style')
        actionCopyStyle.triggered.connect(lambda *args, _lyr=lyr: pasteStyleToClipboard(_lyr))
        menu.addSeparator()

        action = menu.addAction('Copy layer path')
        action.triggered.connect(lambda: QApplication.clipboard().setText(lyr.source()))
        action = menu.addAction('Copy layer to QGIS')
        action.setIcon(QIcon(':/images/themes/default/mActionDuplicateLayer.svg'))
        action.setToolTip('Copy layer to QGIS')
        action.triggered.connect((lambda: self.onCopyLayerToQgisClicked(lyr)))

        action = menu.addAction('Save as...')
        action.triggered.connect(lambda *args, _lyr=lyr: self.onSaveAs(_lyr))

    def addVectorLayerMenuItems(self, node: QgsLayerTreeLayer, menu: QMenu):
        """
        Adds QgsVectorLayer specific menu items
        :param lyr:
        :param menu:
        :return:
        """
        lyr = node.layer()
        from enmapboxprocessing.algorithm.savelibraryasgeojsonalgorithm import SaveLibraryAsGeoJsonAlgorithm

        action = menu.addAction('Save as GeoJSON')
        action.alg = SaveLibraryAsGeoJsonAlgorithm()
        action.parameters = {action.alg.P_LIBRARY: lyr}
        action.triggered.connect(self.onRunProcessingAlgorithmClicked)

        menu.addSeparator()

        action = menu.addAction('Open Attribute Table')
        action.setToolTip('Opens the layer attribute table')
        action.triggered.connect(lambda *args, _lyr=lyr: self.openAttributeTable(_lyr))
        action = menu.addAction('Open Spectral Library Viewer')
        action.setToolTip('Opens the vector layer in a spectral library view')
        action.triggered.connect(lambda *args, _lyr=lyr: self.openSpectralLibraryView(_lyr))

    def addRasterLayerMenuItems(self, node: QgsLayerTreeLayer, menu: QMenu):
        """
        Adds QgsRasterLayer specific menu items
        :param lyr:
        :param menu:
        :return:
        """
        lyr = node.layer()
        from enmapboxprocessing.algorithm.inversetransformrasteralgorithm import InverseTransformRasterAlgorithm
        from enmapboxprocessing.algorithm.predictclassificationalgorithm import PredictClassificationAlgorithm
        from enmapboxprocessing.algorithm.predictclassprobabilityalgorithm import PredictClassPropabilityAlgorithm
        from enmapboxprocessing.algorithm.predictclusteringalgorithm import PredictClusteringAlgorithm
        from enmapboxprocessing.algorithm.predictregressionalgorithm import PredictRegressionAlgorithm
        from enmapboxprocessing.algorithm.transformrasteralgorithm import TransformRasterAlgorithm

        menu.addSeparator()
        # add processing algorithm & application shortcuts
        submenu = menu.addMenu(QIcon(':/images/themes/default/styleicons/color.svg'), 'Statistics and Visualization')

        from bandstatisticsapp import BandStatisticsApp
        action = submenu.addAction(BandStatisticsApp.title())
        action.setIcon(BandStatisticsApp.icon())
        action.triggered.connect(lambda: self.onBandStatisticsClicked(lyr))

        if lyr.bandCount() >= 2:
            from bivariatecolorrasterrendererapp import BivariateColorRasterRendererApp
            action: QAction = submenu.addAction(BivariateColorRasterRendererApp.title())
            action.setIcon(BivariateColorRasterRendererApp.icon())
            action.triggered.connect(lambda: self.onBivariateColorRasterRendererClicked(lyr))

        from classfractionstatisticsapp import ClassFractionStatisticsApp
        action: QAction = submenu.addAction(ClassFractionStatisticsApp.title())
        action.setIcon(ClassFractionStatisticsApp.icon())
        action.triggered.connect(lambda: self.onClassFractionStatisticsClicked(lyr))

        if isinstance(lyr.renderer(), QgsPalettedRasterRenderer):
            from classificationstatisticsapp import ClassificationStatisticsApp
            action = submenu.addAction(ClassificationStatisticsApp.title())
            action.setIcon(ClassificationStatisticsApp.icon())
            action.triggered.connect(lambda: self.onClassificationStatisticsClicked(lyr))

        if lyr.bandCount() >= 3:
            from cmykcolorrasterrendererapp import CmykColorRasterRendererApp
            action = submenu.addAction(CmykColorRasterRendererApp.title())
            action.setIcon(CmykColorRasterRendererApp.icon())
            action.triggered.connect(lambda: self.onCmykColorRasterRendererClicked(lyr))

        if lyr.bandCount() >= 3:
            from colorspaceexplorerapp import ColorSpaceExplorerApp
            action = submenu.addAction(ColorSpaceExplorerApp.title())
            action.setIcon(ColorSpaceExplorerApp.icon())
            action.triggered.connect(lambda: self.onColorSpaceExplorerClicked(lyr))

        if lyr.bandCount() >= 3:
            from decorrelationstretchapp import DecorrelationStretchApp
            action: QAction = submenu.addAction(DecorrelationStretchApp.title())
            action.setIcon(DecorrelationStretchApp.icon())
            action.triggered.connect(lambda: self.onDecorrelationStretchClicked(lyr))

        if lyr.bandCount() >= 3:
            from hsvcolorrasterrendererapp import HsvColorRasterRendererApp
            action = submenu.addAction(HsvColorRasterRendererApp.title())
            action.setIcon(HsvColorRasterRendererApp.icon())
            action.triggered.connect(lambda: self.onHsvColorRasterRendererClicked(lyr))

        if lyr.bandCount() >= 1:
            from multisourcemultibandcolorrendererapp import MultiSourceMultiBandColorRendererApp
            action = submenu.addAction(MultiSourceMultiBandColorRendererApp.title())
            action.setIcon(MultiSourceMultiBandColorRendererApp.icon())
            action.triggered.connect(lambda: self.onMultiSourceMultiBandColorRendererClicked(lyr))

        if lyr.bandCount() >= 2:
            from scatterplotapp import ScatterPlotApp
            action = submenu.addAction(ScatterPlotApp.title())
            action.setIcon(ScatterPlotApp.icon())
            action.triggered.connect(lambda: self.onScatterPlotClicked(lyr))

        # add apply model shortcuts
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox.instance()
        classifiers = list()
        regressors = list()
        transformers = list()
        clusterers = list()
        modelDataSource: ModelDataSource
        for modelDataSource in enmapBox.dataSources('MODEL', False):
            if not isinstance(modelDataSource.mPklObject, dict):
                continue
            if modelDataSource.mPklObject.get('classifier') is not None:
                classifiers.append(modelDataSource)
            if modelDataSource.mPklObject.get('regressor') is not None:
                regressors.append(modelDataSource)
            if modelDataSource.mPklObject.get('transformer') is not None:
                transformers.append(modelDataSource)
            if modelDataSource.mPklObject.get('clusterer') is not None:
                clusterers.append(modelDataSource)
        if len(classifiers + regressors + transformers + clusterers) > 0:
            submenu = menu.addMenu(QIcon(':/images/themes/default/processingAlgorithm.svg'),
                                   'Apply model')
            for classifier in classifiers:
                submenu2 = submenu.addMenu(classifier.name())
                action: QAction = submenu2.addAction('Predict classification layer')
                action.alg = PredictClassificationAlgorithm()
                action.parameters = {
                    action.alg.P_CLASSIFIER: classifier.source(),
                    action.alg.P_RASTER: lyr
                }
                action.triggered.connect(self.onRunProcessingAlgorithmClicked)
                action: QAction = submenu2.addAction('Predict class probability layer')
                action.alg = PredictClassPropabilityAlgorithm()
                action.parameters = {
                    action.alg.P_CLASSIFIER: classifier.source(),
                    action.alg.P_RASTER: lyr
                }
                action.triggered.connect(self.onRunProcessingAlgorithmClicked)
            for regressor in regressors:
                submenu2 = submenu.addMenu(regressor.name())
                action: QAction = submenu2.addAction('Predict regression layer')
                action.alg = PredictRegressionAlgorithm()
                action.parameters = {
                    action.alg.P_REGRESSOR: regressor.source(),
                    action.alg.P_RASTER: lyr
                }
                action.triggered.connect(self.onRunProcessingAlgorithmClicked)
            for transformer in transformers:
                submenu2 = submenu.addMenu(transformer.name())
                action: QAction = submenu2.addAction('Transform raster layer')
                action.alg = TransformRasterAlgorithm()
                action.parameters = {
                    action.alg.P_TRANSFORMER: transformer.source(),
                    action.alg.P_RASTER: lyr
                }
                action.triggered.connect(self.onRunProcessingAlgorithmClicked)
                action: QAction = submenu2.addAction('Inverse transform raster layer')
                action.alg = InverseTransformRasterAlgorithm()
                action.parameters = {
                    action.alg.P_TRANSFORMER: transformer.source(),
                    action.alg.P_RASTER: lyr
                }
                action.triggered.connect(self.onRunProcessingAlgorithmClicked)
            for clusterer in clusterers:
                submenu2 = submenu.addMenu(clusterer.name())
                action: QAction = submenu2.addAction('Predict (unsupervised) classification layer')
                action.alg = PredictClusteringAlgorithm()
                action.parameters = {
                    action.alg.P_CLUSTERER: clusterer.source(),
                    action.alg.P_RASTER: lyr
                }
                action.triggered.connect(self.onRunProcessingAlgorithmClicked)

            action = menu.addAction('Raster Layer Styling')
            action.setToolTip('Open layer in Raster Layer Styling panel')
            action.setIcon(QIcon(':/images/themes/default/propertyicons/symbology.svg'))
            action.triggered.connect(lambda *args, _lyr=lyr: self.onRasterLayerStylingClicked(_lyr))

    def onSaveAs(self, layer: QgsMapLayer):
        """
        Saves vector / raster layers
        """
        emb = self.enmapboxInstance()
        if emb is None:
            return

        if isinstance(layer, QgsRasterLayer):
            from enmapboxprocessing.algorithm.saverasterlayerasalgorithm import SaveRasterAsAlgorithm
            parameters = {SaveRasterAsAlgorithm.P_RASTER: layer}
            dlg = emb.showProcessingAlgorithmDialog(SaveRasterAsAlgorithm(), parameters, parent=None)

        elif isinstance(layer, QgsVectorLayer):
            parameters = dict(INPUT=layer)
            dlg = emb.showProcessingAlgorithmDialog('native:savefeatures', parameters, parent=None)

    def onZoomToLayer(self, lyr: QgsMapLayer, canvas: QgsMapCanvas):
        """
        Zooms a QgsMapCanvas to the extent of a QgsMapLayer
        :param lyr:
        :type lyr:
        :param canvas:
        :type canvas:
        :return:
        :rtype:
        """
        assert isinstance(lyr, QgsMapLayer)
        assert isinstance(canvas, QgsMapCanvas)

        ext = SpatialExtent.fromLayer(lyr).toCrs(canvas.mapSettings().destinationCrs())
        if isinstance(ext, SpatialExtent):
            canvas.setExtent(ext)
        else:
            s = ""

    def openAttributeTable(self, layer: QgsVectorLayer):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox) and isinstance(layer, QgsVectorLayer):
            from enmapbox.gui.dataviews.docks import AttributeTableDock
            emb.createDock(AttributeTableDock, layer=layer)

    def openSpectralLibraryView(self, layer: QgsVectorLayer):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox) and isinstance(layer, QgsVectorLayer):
            from enmapbox.gui.dataviews.docks import SpectralLibraryDock
            emb.createDock(SpectralLibraryDock, speclib=layer)

    def showLayerProperties(self, layer: QgsMapLayer, canvas: QgsMapCanvas):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        messageBar = None
        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox) and isinstance(layer, QgsVectorLayer):
            messageBar = emb.messageBar()
        showLayerPropertiesDialog(layer, canvas=canvas, messageBar=messageBar, modal=True, useQGISDialog=False)

    def onAddGroup(self):
        """
        Create a new layer group
        """
        node = self.mDockTreeView.currentNode()

        newNode = QgsLayerTreeGroup(name='Group')
        if isinstance(node, QgsLayerTree):
            node.insertChildNode(0, newNode)
        elif isinstance(node, (QgsLayerTreeGroup, QgsLayerTreeLayer)):
            parent = node.parent()
            if isinstance(parent, QgsLayerTreeGroup):
                index = parent.children().index(node) + 1
                parent.insertChildNode(index, newNode)

    @typechecked
    def onBandStatisticsClicked(self, layer: QgsRasterLayer):
        from bandstatisticsapp import BandStatisticsDialog
        self.bandStatisticsDialog = BandStatisticsDialog(parent=self.mDockTreeView)
        self.bandStatisticsDialog.show()
        self.bandStatisticsDialog.mLayer.setLayer(layer)
        self.bandStatisticsDialog.mAddRendererBands.click()

    @typechecked
    def onScatterPlotClicked(self, layer: QgsRasterLayer):
        from scatterplotapp import ScatterPlotDialog
        self.scatterPlotDialog = ScatterPlotDialog(parent=self.mDockTreeView)
        self.scatterPlotDialog.show()
        self.scatterPlotDialog.mLayerX.setLayer(layer)
        self.scatterPlotDialog.mLayerY.setLayer(layer)
        self.scatterPlotDialog.mBandX.setBand(1)
        self.scatterPlotDialog.mBandY.setBand(2)

    @typechecked
    def onClassificationStatisticsClicked(self, layer: QgsRasterLayer):
        from classificationstatisticsapp import ClassificationStatisticsDialog
        self.classificationStatisticsDialog = ClassificationStatisticsDialog(parent=self.mDockTreeView)
        self.classificationStatisticsDialog.show()
        self.classificationStatisticsDialog.mLayer.setLayer(layer)

    @typechecked
    def onClassFractionStatisticsClicked(self, layer: QgsRasterLayer):
        from classfractionstatisticsapp import ClassFractionStatisticsDialog
        self.classFractionStatisticsDialog = ClassFractionStatisticsDialog(parent=self.mDockTreeView)
        self.classFractionStatisticsDialog.show()
        self.classFractionStatisticsDialog.mLayer.setLayer(layer)

    @typechecked
    def onColorSpaceExplorerClicked(self, layer: QgsRasterLayer):
        from colorspaceexplorerapp import ColorSpaceExplorerDialog
        self.colorSpaceExplorerDialog = ColorSpaceExplorerDialog(parent=self.mDockTreeView)
        self.colorSpaceExplorerDialog.show()
        self.colorSpaceExplorerDialog.mLayer.setLayer(layer)

    @typechecked
    def onDecorrelationStretchClicked(self, layer: QgsRasterLayer):
        from decorrelationstretchapp import DecorrelationStretchDialog
        self.decorrelationStretchDialog = DecorrelationStretchDialog(parent=self.mDockTreeView)
        self.decorrelationStretchDialog.show()
        self.decorrelationStretchDialog.mLayer.setLayer(layer)

    @typechecked
    def onBivariateColorRasterRendererClicked(self, layer: QgsRasterLayer):
        from bivariatecolorrasterrendererapp import BivariateColorRasterRendererDialog
        self.bivariateColorRasterRendererDialog = BivariateColorRasterRendererDialog(parent=self.mDockTreeView)
        self.bivariateColorRasterRendererDialog.show()
        self.bivariateColorRasterRendererDialog.mLayer.setLayer(layer)

    @typechecked
    def onCmykColorRasterRendererClicked(self, layer: QgsRasterLayer):
        from cmykcolorrasterrendererapp import CmykColorRasterRendererDialog
        self.cmykColorRasterRendererDialog = CmykColorRasterRendererDialog(parent=self.mDockTreeView)
        self.cmykColorRasterRendererDialog.show()
        self.cmykColorRasterRendererDialog.mLayer.setLayer(layer)

    @typechecked
    def onHsvColorRasterRendererClicked(self, layer: QgsRasterLayer):
        from hsvcolorrasterrendererapp import HsvColorRasterRendererDialog
        self.hsvColorRasterRendererDialog = HsvColorRasterRendererDialog(parent=self.mDockTreeView)
        self.hsvColorRasterRendererDialog.show()
        self.hsvColorRasterRendererDialog.mLayer.setLayer(layer)

    @typechecked
    def onMultiSourceMultiBandColorRendererClicked(self, layer: QgsRasterLayer):
        from multisourcemultibandcolorrendererapp import MultiSourceMultiBandColorRendererDialog
        self.multiSourceMultiBandColorRendererDialog = MultiSourceMultiBandColorRendererDialog(
            parent=self.mDockTreeView)
        self.multiSourceMultiBandColorRendererDialog.show()
        self.multiSourceMultiBandColorRendererDialog.mLayer1.setLayer(layer)
        self.multiSourceMultiBandColorRendererDialog.mLayer2.setLayer(layer)
        self.multiSourceMultiBandColorRendererDialog.mLayer3.setLayer(layer)
        self.multiSourceMultiBandColorRendererDialog.onApplyClicked()

    @typechecked
    def onCopyLayerToQgisClicked(self, layer: QgsMapLayer):
        layer2 = layer.clone()
        QgsProject.instance().addMapLayer(layer2, True)

    def onRunProcessingAlgorithmClicked(self):
        from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox.instance()

        action = self.mDockTreeView.sender()
        alg: EnMAPProcessingAlgorithm = action.alg
        parameters: Dict = action.parameters
        enmapBox.showProcessingAlgorithmDialog(alg, parameters, True, True, parent=self.mDockTreeView)

    @typechecked
    def onRasterLayerStylingClicked(self, layer: QgsRasterLayer):
        from rasterlayerstylingapp import RasterLayerStylingApp
        dockPanel: DockPanelUI = self.enmapboxInstance().ui.dockPanel
        dockPanel.mRasterLayerStyling.setChecked(True)
        RasterLayerStylingApp.panel().mLayer.setLayer(layer)


class DockPanelUI(QgsDockWidget):
    mRasterLayerStyling: QToolButton

    def __init__(self, parent=None):
        super(DockPanelUI, self).__init__(parent)
        loadUi(enmapboxUiPath('dockpanel.ui'), self)
        self.mDockManager: DockManager = None
        self.mDockManagerTreeModel: DockManagerTreeModel = None
        self.mMenuProvider: DockManagerLayerTreeModelMenuProvider = None

        self.dockTreeView: DockTreeView
        self.actionRemoveSelected: QAction
        self.btnRemoveSource: QToolButton

        self.btnRemoveSource.setDefaultAction(self.actionRemoveSelected)
        self.actionRemoveSelected.triggered.connect(self.onRemoveSelected)

        self.mRasterLayerStyling.toggled.connect(self.onRasterLayerStylingToggled)
        self.mRasterLayerStyling.setToolTip('Open the Raster Layer Styling panel')

        assert isinstance(self.dockTreeView, DockTreeView)
        # self.dockTreeView.currentLayerChanged.connect(self.onSelectionChanged)
        self.tbFilterText.textChanged.connect(self.setFilter)
        self.initActions()

    def setFilter(self, pattern: str):
        if Qgis.QGIS_VERSION < '3.18':
            return
        proxyModel = self.dockTreeView.proxyModel()
        if isinstance(proxyModel, QgsLayerTreeProxyModel):
            proxyModel.setFilterText(pattern)

    def onRasterLayerStylingToggled(self):
        from rasterlayerstylingapp import RasterLayerStylingApp
        panel = RasterLayerStylingApp.panel()
        if panel is not None:
            panel.setUserVisible(self.mRasterLayerStyling.isChecked())
        if panel.isUserVisible():
            from enmapbox.gui.enmapboxgui import EnMAPBox
            enmapBox = EnMAPBox.instance()
            panel.mLayer.setLayer(enmapBox.currentLayer())

    def onRemoveSelected(self):
        tv: DockTreeView = self.dockTreeView
        model = self.dockManagerTreeModel()
        if isinstance(model, DockManagerTreeModel):
            nodes = tv.selectedNodes()
            dockNodes = [n for n in nodes if isinstance(n, DockTreeNode)]
            layerOrGroup = [n for n in nodes if isinstance(n, (QgsLayerTreeLayer, QgsLayerTreeGroup))
                            and not isinstance(n, DockTreeNode)]

            self.mDockManagerTreeModel.removeNodes(layerOrGroup)

            for n in dockNodes:
                self.mDockManager.removeDock(n.dock)
            # docks = [n.dock for n in self.dockTreeView.selectedNodes() if isinstance(n, DockTreeNode)]
            # for dock in docks:
            #    self.mDockManagerTreeModel.removeDock(dock)

    def initActions(self):
        self.btnCollapse.setDefaultAction(self.actionCollapseTreeNodes)
        self.btnExpand.setDefaultAction(self.actionExpandTreeNodes)

        self.actionCollapseTreeNodes.triggered.connect(self.dockTreeView.collapseAllNodes)
        self.actionExpandTreeNodes.triggered.connect(self.dockTreeView.expandAllNodes)

    def connectDockManager(self, dockManager: DockManager):
        """
        Connects the DockPanelUI with a DockManager
        :param dockManager:
        :return:
        """
        assert isinstance(dockManager, DockManager)
        self.mDockManager = dockManager
        self.mDockManagerTreeModel = DockManagerTreeModel(self.mDockManager)
        # self.mDockManagerProxyModel.setSourceModel(self.mDockManagerTreeModel)
        self.dockTreeView: DockTreeView
        self.dockTreeView.setModel(self.mDockManagerTreeModel)

        m = self.dockTreeView.layerTreeModel()
        assert self.mDockManagerTreeModel == m
        assert isinstance(m, QgsLayerTreeModel)

        self.mMenuProvider: DockManagerLayerTreeModelMenuProvider = DockManagerLayerTreeModelMenuProvider(
            self.dockTreeView)
        self.dockTreeView.setMenuProvider(self.mMenuProvider)

    def dockManagerTreeModel(self) -> DockManagerTreeModel:
        return self.dockTreeView.layerTreeModel()


class MapCanvasBridge(QgsLayerTreeMapCanvasBridge):

    def __init__(self, root: MapDockTreeNode, canvas: QgsMapCanvas, parent=None):
        super(MapCanvasBridge, self).__init__(root, canvas)
        self.setAutoSetupOnFirstLayer(True)
        assert isinstance(root, MapDockTreeNode)
        assert isinstance(canvas, MapCanvas)
        self.mFirstCRS: QgsCoordinateReferenceSystem = None

    def setCanvasLayers(self) -> None:
        canvas: MapCanvas = self.mapCanvas()
        super().setCanvasLayers()

        if not isinstance(self.mFirstCRS, QgsCoordinateReferenceSystem):

            for node in self.rootGroup().findLayers():
                if node.isVisible() and isinstance(node.layer(), QgsMapLayer) and node.layer().crs().isValid():
                    self.mFirstCRS = node.layer().crs()
                    canvas.setDestinationCrs(self.mFirstCRS)
                    canvas.zoomToFullExtent()
                    break


def createDockTreeNode(dock: Dock) -> DockTreeNode:
    """
    Returns a DockTreeNode corresponding to a Dock
    :param dock:
    :param parent:
    :return:
    """
    if isinstance(dock, MapDock):
        return MapDockTreeNode(dock)
    elif isinstance(dock, TextDock):
        return TextDockTreeNode(dock)
    elif isinstance(dock, SpectralLibraryDock):
        return SpeclibDockTreeNode(dock)
    elif isinstance(dock, AttributeTableDock):
        return AttributeTableDockTreeNode(dock)
    elif isinstance(dock, Dock):
        return DockTreeNode(dock)
    return None


class CheckableLayerTreeNode(LayerTreeNode):
    sigCheckStateChanged = pyqtSignal(Qt.CheckState)

    def __init__(self, *args, **kwds):
        super(CheckableLayerTreeNode, self).__init__(*args, **kwds)
        self.mCheckState = Qt.Unchecked

    def setCheckState(self, checkState):
        if isinstance(checkState, bool):
            checkState == Qt.Checked if checkState else Qt.Unchecked
        assert isinstance(checkState, Qt.CheckState)
        old = self.mCheckState
        self.mCheckState = checkState
        if old != self.mCheckState:
            self.sigCheckStateChanged.emit(self.mCheckState)

    def checkState(self):
        return self.mCheckState


class LayerTreeViewMenuProvider(QgsLayerTreeViewMenuProvider):

    def __init__(self, treeView):
        super(LayerTreeViewMenuProvider, self).__init__()
        assert isinstance(treeView, DockTreeView)
        assert isinstance(treeView.layerTreeModel(), DockManagerTreeModel)
        self.treeView = treeView
        self.model = treeView.layerTreeModel()

    def currentNode(self):
        return self.treeView.currentNode()

    def currentIndex(self):
        return self.treeView.currentIndex()

    def currentColumnName(self):
        return self.model.columnNames[self.currentIndex().column()]

    def createContextMenu(self):
        """
        Returns the current nodes contextMenu.
        Overwrite to add TreeViewModel specific logic.
        :return:
        """
        node = self.currentNode()
        if isinstance(node, LayerTreeNode):
            return self.currentNode().populateContextMenu()
        else:
            return QMenu()
