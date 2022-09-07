# -*- coding: utf-8 -*-

"""
***************************************************************************
    vrtbuilderapp

    An EnMAP-Box Application to start the Virtual Raster Builder QGIS Plugin
    see https://bitbucket.org/jakimowb/virtual-raster-builder for details
    ---------------------
    Date                 : October 2017
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

import importlib
import typing
import uuid
import os
from osgeo import gdal
from qgis.PyQt.QtWidgets import QMessageBox, QMainWindow, QMenu
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsRasterRenderer
from qgis.gui import QgsMapCanvas, QgisInterface
import qgis.utils
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.datasources.manager import DataSourceManagerTreeView, RasterBandTreeNode
from enmapbox.gui.dataviews.dockmanager import DockTreeView

APP_DIR = os.path.dirname(__file__)
MIN_VERSION = '0.9'
INSTALLED_VERSION = ''


def vrtBuilderPluginInstalled() -> bool:
    """
    Returns True if the Virtual Raster Builder QGIS Plugin is installed
    :return: bool
    """
    qgis.utils.updateAvailablePlugins()
    return importlib.util.find_spec('vrtbuilder') is not None


if vrtBuilderPluginInstalled():
    import vrtbuilder

    if hasattr(vrtbuilder, '__version__'):
        INSTALLED_VERSION = vrtbuilder.__version__
    elif hasattr(vrtbuilder, 'VERSION'):
        INSTALLED_VERSION = vrtbuilder.VERSION


class VRTBuilderApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super(VRTBuilderApp, self).__init__(enmapBox, parent=parent)
        self.name = 'Virtual Raster Builder'

        self.mIsInstalled = vrtBuilderPluginInstalled()
        self.mInstance = None

        if self.mIsInstalled:
            from vrtbuilder import LICENSE, PATH_ICON
            self.version = 'Version {}'.format(INSTALLED_VERSION)
            self.licence = LICENSE
            self.mIcon = QIcon(PATH_ICON)

            dstv: DataSourceManagerTreeView = self.enmapbox.dataSourceManagerTreeView()
            dstv.sigPopulateContextMenu.connect(
                lambda menu, widget=None: self.onPopulateDataSourceContextMenu(menu, widget))
            dotv: DockTreeView = self.enmapbox.dockTreeView()
            dotv.sigPopulateContextMenu.connect(
                lambda menu, widget=None: self.onPopulateDockTreeContextMenu(menu, widget))

        else:
            self.version = 'Unknown'
            self.licence = 'Unknown'
            self.mIcon = QIcon()

    def icon(self) -> QIcon:
        return QIcon(self.mIcon)

    def menu(self, appMenu):
        """
        Specify menu, submenus and actions
        :return: the QMenu or QAction to be added to the "Applications" menu.
        """
        appMenu = self.enmapbox.menu('Tools')
        a = self.utilsAddActionInAlphanumericOrder(appMenu, self.name)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return None

    def startGUI(self, *args) -> QMainWindow:

        if vrtBuilderPluginInstalled():

            if MIN_VERSION > INSTALLED_VERSION:
                QMessageBox.information(None, 'Outdated Version',
                                        f'Please update the Virtual Raster Builder QGIS Plugin\nto version >= {MIN_VERSION}')
                return None
            else:
                from vrtbuilder.widgets import VRTBuilderWidget
                w = VRTBuilderWidget()
                # show EnMAP-Box raster sources in VRTBuilder
                self.enmapbox.sigRasterSourceAdded.connect(lambda path: w.addSourceFiles([path]))

                # populate VRT Builder with raster files known to the EnMAP-Box
                w.addSourceFiles(self.enmapbox.dataSources('RASTER'))

                # add created virtual raster to EnMAP-Box
                w.sigRasterCreated.connect(self.enmapbox.addSource)

                w.sigAboutCreateCurrentMapTools.connect(self.onSetWidgetMapTool)
                # if False:
                #    dstv: DataSourceTreeView = self.enmapbox.dataSourceTreeView()
                #    dstv.sigPopulateContextMenu.connect(lambda m, widget=w: self.onPopulateDataSourceContextMenu(m, w))
                #    dotv: DockTreeView = self.enmapbox.dockTreeView()
                #    dotv.sigPopulateContextMenu.connect(lambda m, widget=w: self.onPopulateDockTreeContextMenu(m, w))
                w.show()
                return w
        else:
            QMessageBox.information(None, 'Missing QGIS Plugin',
                                    'Please install and activate the Virtual Raster Builder QGIS Plugin.')
            return None

    def onPopulateDataSourceContextMenu(self, menu: QMenu, w):
        assert isinstance(menu, QMenu)

        dstv: DataSourceManagerTreeView = self.enmapbox.dataSourceManagerTreeView()
        bandNodes = [n for n in dstv.selectedNodes() if isinstance(n, RasterBandTreeNode)]
        self.addMenuForInputs(menu, bandNodes, w)

    def onPopulateDockTreeContextMenu(self, menu: QMenu, w):
        assert isinstance(menu, QMenu)

        dotv: DockTreeView = self.enmapbox.dockTreeView()

        selectedRasterLayers = [lyr for lyr in dotv.selectedLayers()
                                if isinstance(lyr, QgsRasterLayer)
                                and lyr.providerType() == 'gdal']

        self.addMenuForInputs(menu, selectedRasterLayers, w)

    def addMenuForInputs(self, menu: QMenu, inputs: typing.List, w):
        if len(inputs) > 0:
            m = menu.addMenu('Create VRT')
            a = m.addAction('Open in Virtual Raster Builder')

            a.triggered.connect(lambda *args, i=inputs, w=True: self.openVRT(i, w))

            a = m.addAction('Create in memory stack')
            a.triggered.connect(lambda *args, ww=w, i=inputs: self.openVRT(i, None, mosaic=False))
            a = m.addAction('Create in memory mosaic')
            a.triggered.connect(lambda *args, ww=w, i=inputs: self.openVRT(i, None, mosaic=True))

    def openVRT(self, inputs, builder, mosaic: bool = False):
        from vrtbuilder.widgets import VRTBuilderWidget
        from vrtbuilder.virtualrasters import VRTRaster, VRTRasterBand, VRTRasterInputSourceBand
        source_bands: typing.List[VRTRasterInputSourceBand] = []
        assert isinstance(inputs, list)
        for src in inputs:
            if isinstance(src, QgsRasterLayer):
                for b in range(src.bandCount()):
                    source_bands.append(VRTRasterInputSourceBand(src.source(), b - 1))

            elif isinstance(src, QgsRasterRenderer):
                for b in src.usesBands():
                    source_bands.append(VRTRasterInputSourceBand(src.source(), b - 1))

            elif isinstance(src, RasterBandTreeNode):
                path = src.mDataSource.uri()
                bandIndex = src.mBandIndex
                source_bands.append(VRTRasterInputSourceBand(path, bandIndex))
            else:
                raise NotImplementedError()
        if isinstance(builder, bool) and builder is True:
            builder = self.startGUI()

        if isinstance(builder, VRTBuilderWidget):
            VRT = builder.mVRTRaster
        else:
            VRT = VRTRaster()
        if mosaic:
            band = VRTRasterBand()
            for srcBand in source_bands:
                band.addSource(srcBand)
            VRT.addVirtualBand(band)
        else:
            for srcBand in source_bands:
                band = VRTRasterBand()
                band.addSource(srcBand)
                VRT.addVirtualBand(band)

        if not isinstance(builder, VRTBuilderWidget):
            path = f'/vsimem/{uuid.uuid4()}.vrt'
            ds: gdal.Dataset = VRT.saveVRT(path)
            if isinstance(ds, gdal.Dataset):
                self.enmapbox.addSource(path)

    def onSetWidgetMapTool(self):
        w = self.sender()

        if not self.mIsInstalled:
            return
        from vrtbuilder.widgets import VRTBuilderWidget
        assert isinstance(w, VRTBuilderWidget)
        canvases = []

        if isinstance(self.enmapbox, EnMAPBox):
            canvases.extend(self.enmapbox.mapCanvases())

        if isinstance(qgis.utils.iface, QgisInterface):
            canvases.extend(qgis.utils.iface.mapCanvases())

        canvases = set(canvases)
        for mapCanvas in canvases:
            assert isinstance(mapCanvas, QgsMapCanvas)
            w.createCurrentMapTool(mapCanvas)


def enmapboxApplicationFactory(enmapBox):
    """
    Returns a list of EnMAPBoxApplications
    :param enmapBox: the EnMAP-Box instance.
    :return: EnMAPBoxApplication | [list-of-EnMAPBoxApplications]
    """
    return [VRTBuilderApp(enmapBox)]
