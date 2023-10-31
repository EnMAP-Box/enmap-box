# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'

import unittest

from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsRasterLayer, QgsProject

from enmapbox.exampledata import enmap
from enmapbox.gui.mapcanvas import MapCanvas
from enmapbox.testing import EnMAPBoxTestCase


class CrosshairTests(EnMAPBoxTestCase):

    def test_crosshair(self):
        # add site-packages to sys.path as done by enmapboxplugin.py

        lyr = QgsRasterLayer(enmap)
        QgsProject.instance().addMapLayer(lyr)
        refCanvas = MapCanvas()
        refCanvas.setLayers([lyr])
        refCanvas.setExtent(lyr.extent())
        refCanvas.setDestinationCrs(lyr.crs())
        refCanvas.show()
        refCanvas.mCrosshairItem.setVisibility(True)
        menu = QMenu()
        refCanvas.populateContextMenu(menu, None)
        menu.show()

        QgsProject.instance().addMapLayer(lyr)
        QgsProject.instance().removeMapLayer(lyr)
        del lyr
        self.assertTrue(refCanvas.mCrosshairItem.rasterGridLayer() is None)

        menu = QMenu()
        refCanvas.populateContextMenu(menu, None)
        self.showGui([refCanvas, menu])

        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":
    unittest.main(buffer=False)
