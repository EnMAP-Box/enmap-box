# -*- coding: utf-8 -*-
"""
***************************************************************************
    test_segfault.py
    ---------------------
    Date                 : Januar 2018
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
# noinspection PyPep8Naming
import unittest

from qgis.PyQt.QtCore import QObject
from qgis.core import QgsExpressionContextGenerator
from qgis.gui import QgisInterface, QgsProcessingContextGenerator

from enmapbox.gui.enmapboxgui import EnMAPBox, EnMAPBoxProject
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects

start_app()


# mini test


class EnMAPBoxTests(EnMAPBoxTestCase):

    def test_segfault(self):
        EMB = EnMAPBox(load_other_apps=False, load_core_apps=False)
        self.assertIsInstance(EnMAPBox.instance(), EnMAPBox)
        self.assertEqual(EMB, EnMAPBox.instance())
        self.assertIsInstance(EMB, QObject)
        self.assertIsInstance(EMB, QgisInterface)
        self.assertIsInstance(EMB, QgsExpressionContextGenerator)
        self.assertIsInstance(EMB, QgsProcessingContextGenerator)
        # EMB.loadExampleData()
        lyr = TestObjects.createRasterLayer()
        # EMB.project().addMapLayer(lyr)
        dock1 = EMB.createMapDock()
        dock1.layerTree().addLayer(lyr)

        # EMB.openExampleData(mapWindows=1)
        EMB.close()

        s = ""

        self.assertTrue(EnMAPBox.instance() is None)


if __name__ == '__main__':
    unittest.main(buffer=False)
