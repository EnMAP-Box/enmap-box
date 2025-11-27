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

import unittest

from enmapbox import initAll
from enmapbox.exampledata import enmap
from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.gui.widgets.createspeclibdialog import CreateSpectralLibraryDialog
from enmapbox.qgispluginsupport.qps.maptools import MapTools
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.utils import fid2pixelindices, SpatialPoint
from enmapbox.testing import EnMAPBoxTestCase, start_app
from enmapboxtestdata import fraction_polygon_l3, fraction_point_singletarget, enmap_srf_library
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer, QgsVectorLayer
from qgis.gui import QgsMapLayerComboBox

start_app()
initAll()


class TestSpeclibs(EnMAPBoxTestCase):

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'development only')
    def test_load_image_profiles(self):
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        EB.loadExampleData()
        EB.setMapTool(MapTools.SpectralProfile)
        self.showGui(EB.ui)
        EB.close()
        QgsProject.instance().removeAllMapLayers()

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking dialog')
    def test_create_spectrallibrary(self):
        d = CreateSpectralLibraryDialog()
        if d.exec_() == QDialog.Accepted:
            sl = d.create_speclib()
            self.assertIsInstance(sl, QgsVectorLayer)
            self.assertTrue(SpectralLibraryUtils.isSpectralLibrary(sl))

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'for gui testing only')
    def test_create_testobject(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        from enmapbox.testing import TestObjects

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        library = TestObjects.createSpectralLibrary(profile_field_names=['profiles'], wlu='nanometers')
        library.setName('MyProfiles1')
        assert SpectralLibraryUtils.isSpectralLibrary(library)
        enmapBox.addSources([library])
        self.showGui(enmapBox.ui)
        enmapBox.close()

    def test_visualization_nodes(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        from enmapbox.testing import TestObjects

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        sl = TestObjects.createSpectralLibrary(profile_field_names=['profiles'], wlu='nanometers')
        sl.setName('MySpeclib')

        sl2 = TestObjects.createSpectralLibrary(profile_field_names=['profiles'], wlu='nanometers')
        sl2.setName('MySpeclib2')
        source = sl.source()
        enmapBox.createSpectralLibraryDock(speclib=sl)
        enmapBox.addSources([sl2])

        self.showGui(enmapBox.ui)
        enmapBox.close()

    @unittest.skip('TEST')
    def test_issue_1036(self):
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        lyrR = QgsRasterLayer(enmap, 'EnMAP')
        lyrV = QgsVectorLayer(fraction_point_singletarget, 'points')
        canvas: MapCanvas = EB.createNewMapCanvas()
        sld: SpectralLibraryDock = EB.createNewSpectralLibrary()
        tree = canvas.layerTree()
        tree.addLayers([lyrV, lyrR])

        testDir = self.createTestOutputDirectory()
        path_fids = testDir / 'fid.tif'
        array, no_fid = fid2pixelindices(lyrR, lyrV, raster_fids=path_fids)
        EB.removeSources()
        self.showGui(EB.ui)
        EB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_issue_1032(self):
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        lyrR = QgsRasterLayer(fraction_polygon_l3, 'EnMAP')
        canvas: MapCanvas = EB.createNewMapCanvas()
        EB.createNewSpectralLibrary()
        tree = canvas.layerTree()
        tree.addLayers([lyrR])
        center = SpatialPoint.fromMapLayerCenter(lyrR)
        EB.ui.optionIdentifyProfile.setChecked(True)
        EB.setCurrentLocation(center, canvas)

        self.showGui(EB.ui)
        EB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_issue_1037(self):
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        speclib = QgsVectorLayer(enmap_srf_library, 'Speclib')
        EB.addSource(speclib)
        del speclib
        self.showGui(EB.ui)
        EB.close()
        QgsProject.instance().removeAllMapLayers()

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'blocking dialogs')
    def test_issue_857(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        cb = QgsMapLayerComboBox()
        cb.setProject(enmapBox.project())
        cb.show()
        layer = QgsRasterLayer(enmap, 'EnMAP')
        enmapBox.onDataDropped([layer])

        self.assertEqual(cb.count(), 1)
        enmapBox.removeMapLayer(layer)
        self.assertEqual(cb.count(), 0)

        self.showGui(enmapBox.ui)
        enmapBox.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":
    unittest.main(buffer=False)
