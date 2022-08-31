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
from qgis.core import QgsRasterLayer, QgsMapLayer, QgsVectorLayer
from qgis.gui import QgsMapCanvas
from qgis.core import QgsMapLayerStore

from enmapbox.qgispluginsupport.qps.cursorlocationvalue import CursorLocationInfoDock
from enmapbox.testing import EnMAPBoxTestCase
from enmapbox.testing import TestObjects
from enmapbox.qgispluginsupport.qps.utils import SpatialPoint


class CursorLocationTest(EnMAPBoxTestCase):

    def webLayers(self) -> list:

        if not self.runsInCI():
            layers = [QgsRasterLayer(TestObjects.uriWMS(), 'OSM', 'wms'),
                      QgsVectorLayer(TestObjects.uriWFS(), 'Berlin', 'WFS')]
        else:
            layers = [TestObjects.createRasterLayer(), TestObjects.createVectorLayer()]
        for lyr in layers:
            self.assertIsInstance(lyr, QgsMapLayer)
            self.assertTrue(lyr.isValid())
        return layers

    def test_layertest(self):

        canvas = QgsMapCanvas()

        # layers = self.webLayers()
        layers = [TestObjects.createRasterLayer(), TestObjects.createVectorLayer()]
        center = SpatialPoint.fromMapLayerCenter(layers[0])
        store = QgsMapLayerStore()
        store.addMapLayers(layers)
        canvas.setLayers(layers)
        cldock = CursorLocationInfoDock()
        self.assertIsInstance(cldock, CursorLocationInfoDock)
        cldock.show()
        cldock.loadCursorLocation(center, canvas)
        point = cldock.cursorLocation()
        self.assertIsInstance(point, SpatialPoint)

        self.showGui(cldock)


if __name__ == "__main__":
    unittest.main(buffer=False)
