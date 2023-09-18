#!python
# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/api.examples.py

    This file shows a couple of examples how to use the EnMAP-Box API
    These examples are used for the API Quick Start in doc/source/APIQuickStart.rst
    ---------------------
    Date                 : January 2018
    Copyright            : (C) 2018 by Benjamin Jakimow
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

# imports
import unittest

from enmapbox.testing import start_app
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMainWindow, QTextEdit, QToolBar, QAction
from qgis.core import QgsFeature, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsPointXY, QgsRectangle
from qgis.gui import QgsMapCanvas

qgsApp = start_app()


class Examples(unittest.TestCase):

    def test_Ex1_StartEnMAPBox(self):

        # start EnMAP-Box instance
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox(None)
        enmapBox.openExampleData(mapWindows=1)

        # access existing EnMAP-Box instance
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox.instance()
        print(enmapBox)

        # load some test data
        enmapBox.openExampleData()

        # close the EnMAP-Box instance
        enmapBox = EnMAPBox.instance()
        enmapBox.close()

        qgsApp.exec_()

    def test_Ex2_DataSources(self):

        from enmapbox.gui.enmapboxgui import EnMAPBox
        EMB = EnMAPBox(None)

        enmapBox = EnMAPBox.instance()

        # add some data sources
        from enmapbox.exampledata import enmap as pathRasterSource
        from enmapbox.exampledata import landcover_polygon as pathVectorSource
        from enmapbox.exampledata import library_sli as pathSpectralLibrary

        # add a single source
        enmapBox.addSource(pathRasterSource)

        # add a list of sources
        enmapBox.addSources([pathVectorSource, pathSpectralLibrary])

        # add some Web Services
        wmsUri = 'referer=OpenStreetMap%20contributors,%20under%20ODbL&type=xyz&url=http://tiles.wmflabs.org/hikebike/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=17&zmin=1'
        wfsUri = r'restrictToRequestBBOX=''1'' srsname=''EPSG:25833'' typename=''fis:re_postleit'' url=''http://fbinter.stadt-berlin.de/fb/wfs/geometry/senstadt/re_postleit'' version=''auto'''
        enmapBox.addSource(wmsUri, name="Open Street Map")
        enmapBox.addSource(wfsUri, name='Berlin PLZ')

        # be informed over new data sources
        def onDataSourceAdded(dataSource: str):
            print('DataSource added: {}'.format(dataSource))

        enmapBox.sigDataSourcesAdded.connect(onDataSourceAdded)

        def onDataSourceRemoved(dataSource: str):
            print('DataSource removed: {}'.format(dataSource))

        enmapBox.sigDataSourcesRemoved.connect(onDataSourceRemoved)

        # print all sources
        for source in enmapBox.dataSources():
            print(source)

        # print specific sources only:
        for source in enmapBox.dataSources('RASTER'):
            print(source)

        # remove all data sources
        allSources = enmapBox.dataSources()
        enmapBox.removeSources(allSources)

        # pro tip: access the DataSource objects directly

        qgsApp.exec_()

    def test_Ex2_UniqueDataSources(self):

        from enmapbox.gui.enmapboxgui import EnMAPBox
        from enmapbox.exampledata import enmap

        enmapBox = EnMAPBox(None)
        enmapBox.addSource(enmap)
        print('# data sources: {}'.format(len(enmapBox.dataSources())))

        # add the same source again
        enmapBox.addSource(enmap)
        print('# data sources: {}'.format(len(enmapBox.dataSources())))

    def test_Ex2_DataSource_Versions(self):

        from enmapbox.gui.enmapboxgui import EnMAPBox

        enmapBox = EnMAPBox(None)
        enmapBox.sigDataSourcesAdded.connect(lambda uri: print('DataSource added: {}'.format(uri)))
        enmapBox.sigDataSourcesRemoved.connect(lambda uri: print('DataSource removed: {}'.format(uri)))

        import tempfile
        import os
        import time
        tempDir = tempfile.mkdtemp()
        pathFile = os.path.join(tempDir, 'testfile.txt')

        with open(pathFile, 'w', encoding='utf-8') as f:
            f.write('First version')

        assert os.path.isfile(pathFile)
        enmapBox.addSource(pathFile)
        assert len(enmapBox.dataSources()) == 1

        time.sleep(2)

        with open(pathFile, 'w', encoding='utf-8') as f:
            f.write('Second version')

        assert os.path.exists(pathFile)
        enmapBox.addSource(pathFile)
        assert len(enmapBox.dataSources()) == 1

    def test_Ex3_Docks(self):
        """
        Add new dock windows to view data
        """
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox(None)

        # enmapBox.createDock('MAP')  # a spatial map
        # enmapBox.createDock('SPECLIB') # a spectral library
        # enmapBox.createDock('TEXT') # a text editor
        # enmapBox.createDock('MIME') # a window to drop mime data

        # modify dock properties
        mapDock1 = enmapBox.createDock('MAP')  # two spatial maps
        mapDock2 = enmapBox.createDock('MAP')  # a spatial map
        mapDock3 = enmapBox.createDock('MAP')  # a spatial map

        # set dock title
        mapDock1.setTitle('Map 1 (fixed)')
        mapDock2.setTitle('Map 2 (floated)')
        mapDock3.setTitle('Map 3 (hidden)')

        mapDock2.float()
        mapDock3.setVisible(False)

        # list all docks
        from enmapbox.gui.dataviews.docks import Dock
        for dock in enmapBox.mDockManager.docks():
            assert isinstance(dock, Dock)
            print(dock)

        # list map docks only
        for dock in enmapBox.mDockManager.docks(dockType='MAP'):
            assert isinstance(dock, Dock)
            print(dock)

        # list all spectral library docks
        for dock in enmapBox.mDockManager.docks(dockType='SPECLIB'):
            assert isinstance(dock, Dock)
            print(dock)

        qgsApp.exec_()

    def test_Ex4_MapTools(self):

        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox(None)
        enmapBox.loadExampleData()  # this opens a map dock as well

        from enmapbox.gui import MapTools, SpatialPoint, SpectralProfile

        def printLocation(spatialPoint: SpatialPoint):
            print('Mouse clicked on {}'.format(spatialPoint))

        enmapBox.sigCurrentLocationChanged.connect(printLocation)
        enmapBox.setMapTool(MapTools.CursorLocation)

        def printLocationAndCanvas(spatialPoint: SpatialPoint, canvas: QgsMapCanvas):
            print('Mouse clicked on {} in {}'.format(spatialPoint, canvas))

        enmapBox.sigCurrentLocationChanged[object, QgsMapCanvas].connect(printLocationAndCanvas)

        def printSpectralProfiles(currentSpectra: list):
            print('{} SpectralProfiles collected'.format(len(currentSpectra)))
            for i, p in enumerate(currentSpectra):
                assert isinstance(p, QgsFeature)
                p = SpectralProfile.fromSpecLibFeature(p)
                assert isinstance(p, SpectralProfile)
                print('{}: {}'.format(i + 1, p.values()['y']))

        enmapBox.sigCurrentSpectraChanged.connect(printSpectralProfiles)

        print('Last location: {}'.format(enmapBox.currentLocation()))
        print('Last SpectralProfile: {}'.format(enmapBox.currentSpectra()))

        lastPosition = enmapBox.currentLocation()

        qgsApp.exec_()

    def test_ActivateMapToolsFromExternalApplication(self):

        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox(None)
        enmapBox.loadExampleData()  # this opens a map dock as well

        from enmapbox.gui import SpectralProfile

        class MyApp(QMainWindow):

            def __init__(self, enmapbox: EnMAPBox, *args, **kwds):
                super(MyApp, self).__init__(*args, **kwds)
                self.setWindowTitle('My Application Window')

                self.mEnMAPBox = enmapbox
                self.mEnMAPBox.sigCurrentSpectraChanged.connect(self.onSpectralProfilesCollected)

                self.mToolBar = QToolBar()
                self.addToolBar(self.mToolBar)
                self.mTextBox = QTextEdit()
                self.mTextBox.setLineWrapMode(QTextEdit.NoWrap)
                self.setCentralWidget(self.mTextBox)

                self.mActionGetProfiles = QAction('Collect Profiles')
                self.mActionGetProfiles.setCheckable(True)
                self.mActionGetProfiles.setChecked(False)
                self.mActionGetProfiles.setIcon(QIcon(':/qps/ui/icons/profile_identify.svg'))
                self.mActionGetProfiles.setText('Click to collect spectral profile from the EnMAP-Box')
                self.mActionGetProfiles.triggered.connect(self.onActivateProfileCollection)
                self.mToolBar.addAction(self.mActionGetProfiles)

            def onActivateProfileCollection(self):

                if isinstance(self.mEnMAPBox, EnMAPBox) and self.mActionGetProfiles.isChecked():
                    self.mEnMAPBox.ui.actionIdentify.trigger()
                    self.mEnMAPBox.ui.optionIdentifyProfile.setChecked(True)

                    # soon: self.mEnMAPBox.setMapTool(MapTools.SpectralProfile)

            def onSpectralProfilesCollected(self, spectalProfiles):

                if self.mActionGetProfiles.isChecked():
                    for p in spectalProfiles:
                        assert isinstance(p, QgsFeature)
                        p = SpectralProfile.fromSpecLibFeature(p)
                        self.mTextBox.append(str(p.yValues()))

        myApp = MyApp(enmapBox)
        myApp.show()

        qgsApp.exec_()

    def test_Ex5_PointsAndExtents(self):

        from enmapbox.exampledata import enmap
        from enmapbox.gui import SpatialPoint

        layer = QgsRasterLayer(enmap)
        point = SpatialPoint.fromMapLayerCenter(layer)

        targetCrs = QgsCoordinateReferenceSystem('EPSG:4326')

        print('Original CRS: "{}"'.format(layer.crs().description()))
        print('QgsPointXY  : {}'.format(QgsPointXY(point)))
        print('SpatialPoint: {}\n'.format(point))

        pointTargetCRS = point.toCrs(targetCrs)
        print('Target CRS  : "{}"'.format(targetCrs.description()))
        print('QgsPointXY  : {}'.format(QgsPointXY(pointTargetCRS)))
        print('SpatialPoint: {}\n'.format(pointTargetCRS))

        from enmapbox.gui import SpatialExtent
        extent = SpatialExtent.fromLayer(layer)
        print('Original CRS : "{}"'.format(layer.crs().description()))
        print('QgsRectangle : {}'.format(QgsRectangle(extent)))
        print('SpatialExtent: {}\n'.format(extent))

        extentTargetCRS = extent.toCrs(targetCrs)
        print('Target CRS   : "{}"'.format(targetCrs.description()))
        print('QgsRectangle : {}'.format(QgsPointXY(pointTargetCRS)))
        print('SpatialExtent: {}\n'.format(extentTargetCRS))


if __name__ == "__main__":
    unittest.main()
