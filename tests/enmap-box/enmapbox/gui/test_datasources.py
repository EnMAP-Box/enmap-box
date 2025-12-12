# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'benjamin.jakimow@geo.hu-berlin.de'
__date__ = '2017-07-17'
__copyright__ = 'Copyright 2017, Benjamin Jakimow'

import datetime
import pathlib
import tempfile
import unittest
from pathlib import Path
from time import sleep

from osgeo import ogr

from enmapbox import initAll, DIR_REPO
from enmapbox.exampledata import enmap, hires, landcover_polygon
from enmapbox.gui.datasources.datasources import SpatialDataSource, DataSource, RasterDataSource, VectorDataSource, \
    FileDataSource
from enmapbox.gui.datasources.manager import DataSourceManager, DataSourceManagerPanelUI, DataSourceFactory
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import TestObjects, EnMAPBoxTestCase
from enmapbox.testing import start_app
from enmapboxtestdata import classifierDumpPkl, library_berlin, enmap_srf_library
from qgis.PyQt import sip
from qgis.core import QgsProject, QgsMapLayer, QgsRasterLayer, QgsVectorLayer, QgsRasterRenderer, edit
from qgis.gui import QgsMapCanvas

start_app()
initAll()


class DataSourceTests(EnMAPBoxTestCase):

    def createTestSources(self) -> list:

        # return [library, self.wfsUri, self.wmsUri, enmap, landcover_polygons]
        return [library_berlin, enmap, landcover_polygon]

    def createTestSourceLayers(self) -> list:

        # return [QgsRasterLayer(enmap), QgsVectorLayer(landcover_polygons), SpectralLibrary.readFrom(library)]
        return [TestObjects.createRasterLayer(),
                TestObjects.createVectorLayer(ogr.wkbPoint),
                TestObjects.createVectorLayer(ogr.wkbPolygon),
                TestObjects.createSpectralLibrary(10)]

    def test_testSources(self):

        for lyr in self.createTestSourceLayers():
            self.assertIsInstance(lyr, QgsMapLayer)
            self.assertTrue(lyr.isValid())

    def test_layerSourceUpdate(self):

        path = '/vsimem/image.bsq'
        path = tempfile.mktemp(suffix='image.tif')
        TestObjects.createRasterDataset(nb=5, nl=500, path=path)
        c = QgsMapCanvas()
        c.show()
        lyr = QgsRasterLayer(path)
        r = lyr.renderer()
        self.assertIsInstance(r, QgsRasterRenderer)
        r.setInput(lyr.dataProvider())
        r.setGreenBand(5)

        c.setDestinationCrs(lyr.crs())
        c.setExtent(lyr.extent())
        c.setLayers([lyr])
        c.waitWhileRendering()

        self.assertIsInstance(lyr, QgsRasterLayer)
        self.assertTrue(lyr.isValid())
        self.assertEqual(lyr.bandCount(), 5)
        self.assertEqual(lyr.height(), 500)

        # del lyr

    def test_datasourcemanager_equalsources(self):

        p1 = str(pathlib.Path(hires))
        p2 = pathlib.Path(hires).as_posix()

        dsm = DataSourceManager()
        dsm.addDataSources([p1, p2])
        self.assertTrue(len(dsm) == 1)

        dsm = DataSourceManager()
        dsm.addDataSources([p2, p1])
        self.assertTrue(len(dsm) == 1)

    def test_DataSourcePanelUI(self):

        dsm = DataSourceManager()
        panel = DataSourceManagerPanelUI()
        panel.connectDataSourceManager(dsm)
        uris = [library_berlin, enmap, landcover_polygon]
        dsm.addDataSources(uris)
        self.showGui(panel)

    def test_node_updates(self):

        DM = DataSourceManager()
        DM.mUpdateTimer.stop()

        lyrV: QgsVectorLayer = TestObjects.createSpectralLibrary()

        testDir = self.createTestOutputDirectory()

        path_rl = testDir / 'test_raster.tiff'

        lyrR = TestObjects.createRasterLayer(path=path_rl)

        DM.project().addMapLayer(lyrV)
        DM.project().addMapLayer(lyrR)

        pathTxt = testDir / 'example.txt'
        with open(pathTxt, 'w', encoding='utf-8') as f:
            f.write('Test')

        DM.addDataSources([lyrV, lyrR, pathTxt])
        DM.updateSourceNodes()

        sources = DM.dataSources()
        self.assertTrue(len(sources) == 3)
        for ds in sources:
            self.assertIsInstance(ds.updateTime(), datetime.datetime)

        ds1, ds2, ds3 = sources
        self.assertIsInstance(ds1, RasterDataSource)
        self.assertIsInstance(ds2, VectorDataSource)
        self.assertIsInstance(ds3, FileDataSource)
        t0_1 = ds1.updateTime()
        t0_2 = ds2.updateTime()
        t0_3 = ds3.updateTime()

        with edit(lyrV):
            fids = lyrV.allFeatureIds()
            lyrV.deleteFeatures(fids[0:1])

        DM.updateSourceNodes()
        self.assertTrue(ds1.updateTime() == t0_1)
        self.assertTrue(ds2.updateTime() > t0_2)
        self.assertTrue(ds3.updateTime() == t0_3)

        sleep(1)
        # touch the raster file and the text file
        # to change the file modification time
        Path(ds1.source()).touch()
        Path(ds3.source()).touch()

        DM.updateSourceNodes()
        self.assertTrue(ds1.updateTime() > t0_1)
        self.assertTrue(ds3.updateTime() > t0_3)
        DM.project().removeAllMapLayers()

    def test_DataSourceModel(self):

        sources = [enmap,
                   enmap,
                   landcover_polygon,
                   landcover_polygon,
                   enmap_srf_library,
                   enmap_srf_library,
                   library_berlin,
                   classifierDumpPkl]

        model = DataSourceManager()

        panel = DataSourceManagerPanelUI()
        panel.connectDataSourceManager(model)

        for source in sources:
            dataSources = DataSourceFactory.create(source)
            self.assertIsInstance(dataSources, list)
            model.addDataSources(dataSources)
        self.showGui(panel)

    def test_memory_provider(self):
        uri = "point?crs=epsg:4326&field=id:integer"
        lyr1 = QgsVectorLayer(uri, "Scratch point layer", "memory")

        project = QgsProject()
        project.addMapLayer(lyr1)

        sources = DataSourceFactory.create(lyr1, project=project)
        self.assertTrue(len(sources) == 1)
        ds1 = sources[0]

        self.assertIsInstance(ds1, SpatialDataSource)

        lyr2 = ds1.asMapLayer(project=project)

        self.assertEqual(lyr1, lyr2)

    def test_file_types(self):
        # can we drag & drop ENVI BSQ images?
        # see https://github.com/EnMAP-Box/enmap-box/issues/1382

        from enmapbox.exampledata import enmap

        testdata = Path(DIR_REPO) / 'enmapbox/qgispluginsupport/qpstestdata/wavelength'
        assert testdata.is_dir()

        files = [enmap, hires,
                 testdata / 'envi_wl_fwhm.bsq']

        EMB = EnMAPBox(load_core_apps=False, load_other_apps=False)

        for i, file in enumerate(files):
            self.assertTrue(Path(file).is_file())
            EMB.addSource(file)
            self.assertEqual(i + 1, len(EMB.dataSources('RASTER')))
        self.showGui(EMB.ui)
        EMB.close()

    def test_datasourcemanager(self):
        reg = QgsProject.instance()
        reg.removeAllMapLayers()
        dsm = DataSourceManager()
        uris = [enmap_srf_library, enmap, landcover_polygon]
        uris = [pathlib.Path(p).as_posix() for p in uris]
        dsm.addDataSources(uris)

        self.assertTrue((len(dsm) == len(uris)))
        dsm.addDataSources(uris)
        self.assertEqual(len(dsm), len(uris), msg='Redundant sources are not allowed')

        self.assertEqual(len(dsm.dataSources('SPATIAL')), 3)
        self.assertEqual(len(dsm.dataSources('RASTER')), 1)
        self.assertEqual(len(dsm.dataSources('VECTOR')), 2)
        self.assertEqual(len(dsm.dataSources('SPECLIB')), 1)
        self.assertEqual(len(dsm.dataSources('FILE')), 0)

        self.assertTrue(len(reg.mapLayers()) == 0)
        lyrs = self.createTestSourceLayers()
        dsm = DataSourceManager()
        for i, n in enumerate(lyrs):
            print('Add {}...'.format(n.source()))
            ds = dsm.addDataSources(n)
            self.assertEqual(len(ds), 1)
            self.assertIsInstance(ds[0], DataSource)
            self.assertEqual(len(dsm), i + 1)
        dsm.addDataSources(lyrs)
        self.assertTrue(len(dsm) == len(lyrs))

        dsm = DataSourceManager()
        reg.addMapLayers(lyrs)
        self.assertTrue((len(dsm) == 0))

        reg.removeAllMapLayers()

        # test doubled input
        n = len(dsm)
        try:
            p1 = str(pathlib.WindowsPath(pathlib.Path(enmap)))
            p2 = str(pathlib.Path(enmap).as_posix())
            dsm.addDataSources(p1)
            dsm.addDataSources(p2)
            self.assertTrue(len(dsm) == n, msg='DataSourceManager should not contain the same source multiple times')
        except Exception as ex:
            pass

        # remove
        dsm = DataSourceManager()
        lyr = TestObjects.createVectorLayer()
        dsm.addDataSources(lyr)
        self.assertTrue(len(dsm) == 1)
        QgsProject.instance().addMapLayer(lyr)
        self.assertTrue(len(dsm) == 1)

        self.assertFalse(sip.isdeleted(lyr))
        QgsProject.instance().removeMapLayer(lyr)
        self.assertTrue(sip.isdeleted(lyr))
        # self.assertTrue(len(dsm) == 0)

    def test_registryresponse(self):

        from enmapbox.gui.mapcanvas import MapCanvas
        mapCanvas = MapCanvas()
        reg = QgsProject.instance()
        reg.removeAllMapLayers()

        for p in self.createTestSources():
            print(p)
            ds = DataSourceFactory.create(p)
            if isinstance(ds, SpatialDataSource):
                lyr = ds.createUnregisteredMapLayer()
                mapCanvas.setLayers(lyr)

                self.assertTrue(len(mapCanvas.layers()) == 1)

                self.assertTrue(len(reg.mapLayers()) == 1)
                reg.removeAllMapLayers()
                self.assertTrue(len(mapCanvas.layers()) == 0)

    sublayer_raster_file = r'R:/Rohdaten/EnMAP-Box external Sensor Products/sentinel2/S2A_MSIL2A_20200816T101031_N0214_R022_T32UQD_20200816T130108.SAFE/MTD_MSIL2A.xml'

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'Blocking Dialog')
    @unittest.skipIf(not pathlib.Path(sublayer_raster_file).is_file(), 'blocking dialog/Missing test file')
    def test_sublayers_issue_1214(self):

        lyr = QgsRasterLayer(self.sublayer_raster_file)
        self.assertTrue(len(lyr.subLayers()) > 0)
        for ds in DataSourceFactory.create(self.sublayer_raster_file):
            self.assertIsInstance(ds, RasterDataSource)


if __name__ == "__main__":
    unittest.main(buffer=False)
