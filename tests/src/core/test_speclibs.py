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

from qgis.core import QgsFeature

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.exampledata import enmap, enmap_srf_library
from enmapbox.gui.dataviews.docks import SpectralLibraryDock
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import encodeProfileValueDict
from enmapbox.qgispluginsupport.qps.utils import fid2pixelindices, SpatialPoint
from enmapbox.testing import EnMAPBoxTestCase
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsRasterLayer, QgsVectorLayer
from enmapboxtestdata import fraction_polygon_l3, fraction_point_singletarget


class TestSpeclibs(EnMAPBoxTestCase):

    def setUp(self):
        self.closeEnMAPBoxInstance()

    def tearDown(self):
        self.closeEnMAPBoxInstance()

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

        self.showGui(EB.ui)

    def test_issue_851(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        dock: SpectralLibraryDock = enmapBox.dockManager().createDock('SPECLIB')
        speclib = dock.speclib()
        f = QgsFeature(speclib.fields())

        d = dict(x=[2010, 2020], y=[0, 10000], xUnit='DecimalYear')
        f.setAttribute('profiles', encodeProfileValueDict(d, f.fields().field('profiles')))
        speclib.startEditing()
        speclib.addFeature(f)
        self.assertTrue(speclib.commitChanges())
        self.showGui(enmapBox.ui)

    def test_issue_1032(self):
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        lyrR = QgsRasterLayer(fraction_polygon_l3, 'EnMAP')
        canvas: MapCanvas = EB.createNewMapCanvas()
        sld: SpectralLibraryDock = EB.createNewSpectralLibrary()
        tree = canvas.layerTree()
        tree.addLayers([lyrR])
        center = SpatialPoint.fromMapLayerCenter(lyrR)
        EB.ui.optionIdentifyProfile.setChecked(True)
        EB.setCurrentLocation(center, canvas)

        self.showGui(EB.ui)

    def test_issue_1037(self):
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        speclib = QgsVectorLayer(enmap_srf_library, 'Speclib')
        EB.addSource(speclib)
        del speclib
        self.showGui(EB.ui)

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


if __name__ == "__main__":
    unittest.main(buffer=False)
