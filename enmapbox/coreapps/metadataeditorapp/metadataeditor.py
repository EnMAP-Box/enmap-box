# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/userinterfaces.py

    Some exemplary (graphical) user interfaces, making use of the Qt framework.
    ---------------------
    Date                 : Juli 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import pathlib
from typing import Dict

from enmapbox.gui.datasources.datasources import DataSourceTypes
from qgis.PyQt.QtWidgets import QVBoxLayout, QDialogButtonBox, QDialog
from qgis.PyQt.QtCore import Qt
from enmapbox.qgispluginsupport.qps.layerconfigwidgets.gdalmetadata import GDALMetadataModelConfigWidget
from enmapbox.gui.utils import loadUi
from enmapbox.gui.enmapboxgui import EnMAPBox, SpatialDataSource

from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer, QgsRasterLayer
from qgis.gui import QgsMapLayerComboBox


class MetadataEditorDialogProject(QgsProject):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        QgsProject.instance().layersAdded.connect(self.updateSources)
        QgsProject.instance().layersRemoved.connect(self.updateSources)

        self.mEnMAPBox = None
        self.mDataSources: Dict[str, QgsMapLayer] = dict()
        self.mDataSourceLayerInstances: Dict[str, int] = dict()

    def setEnMAPBox(self, enmapbox: EnMAPBox):
        self.mEnMAPBox = enmapbox
        self.mEnMAPBox.sigDataSourcesAdded.connect(self.updateSources)
        self.mEnMAPBox.sigDataSourcesRemoved.connect(self.updateSources)
        self.updateSources()

    def dataSourceLayer(self, uri: str) -> QgsMapLayer:
        return self.mDataSources.get(uri, None)

    def dataSourceReferences(self, uri: str) -> int:
        return self.mDataSourceLayerInstances.get(uri, 0)

    def updateSources(self):
        datasource_layers: Dict[str, QgsMapLayer] = dict()

        if self.mEnMAPBox:
            layers = []
            for datasource in self.mEnMAPBox.dataSourceManager().dataSources(DataSourceTypes.Spatial):
                if isinstance(datasource, SpatialDataSource):
                    lyr = datasource.asMapLayer()
                    if lyr.isValid():
                        layers.append(lyr)
        else:
            layers = list(QgsProject.instance().mapLayers().values())

        for layer in layers:
            if isinstance(layer, (QgsRasterLayer, QgsVectorLayer)) \
                    and layer.isValid() \
                    and layer.dataProvider().name() in ['gdal', 'ogr']:
                datasource_layers[layer.dataProvider().dataSourceUri()] = layer
        existing_sources = set([lyr.dataProvider().dataSourceUri() for lyr in self.mapLayers().values()])
        to_remove = [s for s in existing_sources if s not in datasource_layers.keys()]
        to_add = [s for s in datasource_layers.keys() if s not in existing_sources]
        if len(to_remove) > 0:
            fids = [fid for fid, lyr in self.mapLayers().items() if lyr.dataProvider().dataSourceUri() in to_remove]
            self.removeMapLayers(fids)
        if len(to_add) > 0:
            self.addMapLayers([datasource_layers[s] for s in to_add])
        self.mDataSources.clear()
        self.mDataSources.update(datasource_layers)

        self.mDataSourceLayerInstances.clear()
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.isValid():
                uri = lyr.dataProvider().dataSourceUri()
                self.mDataSourceLayerInstances[uri] = self.mDataSourceLayerInstances.get(uri, 0) + 1


class MetadataEditorDialog(QDialog):
    """Constructor."""

    def __init__(self, parent=None):
        super(MetadataEditorDialog, self).__init__(parent, Qt.Window)
        path = pathlib.Path(__file__).parent / 'metadataeditor.ui'
        loadUi(path, self)
        assert isinstance(self.cbSource, QgsMapLayerComboBox)

        self.mProject = MetadataEditorDialogProject()
        self.cbSource: QgsMapLayerComboBox
        self.cbSource.setAllowEmptyLayer(True)
        self.cbSource.setProject(self.mProject)
        self.cbSource.layerChanged.connect(self.setLayer)

        self.mdWidget: GDALMetadataModelConfigWidget = GDALMetadataModelConfigWidget(layer=self.cbSource.currentLayer())

        self.frame.setLayout(QVBoxLayout())
        self.frame.layout().addWidget(self.mdWidget)
        self.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.mdWidget.apply)

        # so far, disable editing, viewer only
        self.setWindowTitle('Metadata Viewer')
        self.mdWidget.setEditable(False)
        self.buttonBox.button(QDialogButtonBox.Save).setVisible(False)

    def setEnMAPBox(self, enmapBox):
        self.mProject.setEnMAPBox(enmapBox)

    def setLayer(self, layer: QgsMapLayer):
        if isinstance(layer, QgsMapLayer) and layer.isValid():
            uri = layer.dataProvider().dataSourceUri()
            lyr = self.mProject.dataSourceLayer(uri)
            if isinstance(lyr, QgsMapLayer):
                refCount = self.mProject.dataSourceReferences(uri)
                self.mdWidget.setLayer(layer)
                if refCount == 0:
                    self.mdWidget.setEditable(True)
                else:
                    self.mdWidget.setEditable(False)
        else:
            self.mdWidget.setLayer(None)
