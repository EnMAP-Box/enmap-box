# -*- coding: utf-8 -*-
"""
***************************************************************************
    test_settings
    ---------------------
    Date                 : February 2020
    Copyright            : (C) 2020 by Benjamin Jakimow
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
import os
# noinspection PyPep8Naming
import unittest

from enmapbox import EnMAPBox
from enmapbox.settings import enmapboxSettings, EnMAPBoxSettings
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProject


class TestEnMAPBoxPlugin(EnMAPBoxTestCase):

    def test_loadSettings(self):
        s1 = enmapboxSettings()
        s2 = EnMAPBoxSettings()
        self.assertIsInstance(s1, EnMAPBoxSettings)
        self.assertIsInstance(s2, EnMAPBoxSettings)
        self.assertIsInstance(s2.value(EnMAPBoxSettings.MAP_BACKGROUND), QColor)
        print(s1)

    def setUp(self):
        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox):
            emb.close()

        QgsProject.instance().removeAllMapLayers()

    def test_enmapbox_settings(self):

        box = EnMAPBox(load_core_apps=False, load_other_apps=False)
        box.loadExampleData()
        dataSources = box.dataSources()
        n_maps = len(box.mapCanvases())

        proj = QgsProject.instance()
        self.assertIsInstance(proj, QgsProject)
        tmp_path = self.tempDir() / 'project.qgs'
        os.makedirs(tmp_path.parent, exist_ok=True)

        box.saveProject(tmp_path)

        box.close()
        self.assertTrue(EnMAPBox.instance() is None)

        box = EnMAPBox()
        self.assertIsInstance(box, EnMAPBox)
        box.addProject(tmp_path.as_posix())

        if False:
            self.assertEqual(dataSources, box.dataSources())
            self.assertEqual(n_maps, len(box.mapCanvases()))


if __name__ == '__main__':
    unittest.main(buffer=False)
