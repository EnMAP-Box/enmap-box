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
import pathlib
import sys
# noinspection PyPep8Naming
import unittest

from enmapbox.gui.datasources.datasources import DataSource
from enmapbox.gui.dataviews.docks import MapDock, Dock
from qgis.PyQt.QtGui import QIcon

from enmapbox.enmapboxsettings import enmapboxSettings, EnMAPBoxSettings, EnMAPBoxOptionsFactory
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProject, QgsVectorLayer

from enmapbox.testing import start_app

start_app()


class TestEnMAPBoxSettings(EnMAPBoxTestCase):

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

    def test_enmapbox_setting_dialog(self):
        from enmapbox.enmapboxsettings import EnMAPBoxSettingsPage

        page = EnMAPBoxSettingsPage()

        self.showGui(page)

    def test_enmapbox_optionsFactory(self):

        f = EnMAPBoxOptionsFactory()

        from qgis.utils import iface
        iface.registerOptionsWidgetFactory(f)
        self.assertIsInstance(f.icon(), QIcon)
        self.assertIsInstance(f.key(), str)
        self.assertEqual(f.title(), 'EnMAP-Box')
        w = f.createWidget(None)

        icon = f.icon()

        self.showGui(w)

    def test_enmapbox_project_settings(self):

        proj_old = QgsProject.instance()
        proj = QgsProject()
        proj.setTitle('test_project_settings')
        self.assertIsInstance(proj, QgsProject)
        tmp_path = self.tempDir() / 'project.qgs'
        os.makedirs(tmp_path.parent, exist_ok=True)
        self.assertTrue(proj.write(tmp_path.as_posix()))

        self.assertTrue(tmp_path.is_file())

        QgsProject.setInstance(proj)

        import enmapbox
        enmapbox.RAISE_ALL_EXCEPTIONS = True

        def projectXml() -> str:
            path = pathlib.Path(QgsProject.instance().fileName())
            if path.is_file():
                with open(path, 'r', encoding='utf8') as f:
                    lines = f.read()
                return lines
            else:
                return ''

        def dataSourceState(box: EnMAPBox):
            states = []
            for ds in box.dataSources(onlyUri=False):
                ds: DataSource
                if ds.dataItem().providerKey() != 'memory':
                    states.append(ds.source())
            return states

        def dataViewState(box: EnMAPBox):
            states = []
            for dock in box.docks():
                state = {'name': dock.name(),
                         'type': dock.__class__.__name__}
                states.append(state)
            return states

        box = EnMAPBox(load_core_apps=False, load_other_apps=False)

        from enmapboxtestdata import library_berlin
        speclib = QgsVectorLayer(pathlib.Path(library_berlin).as_posix())
        box.loadExampleData()

        dock1: Dock = box.docks(MapDock)[0]
        dock1.setTitle('MyMap1')
        dock2 = box.createMapDock(name='MyMap2', position='left')
        dock3 = box.createSpectralLibraryDock(name='MySpeclib1', speclib=speclib, position='bottom')
        dock4 = box.createDock('TEXT', name='MyText1', position='top')
        dock4.textDockWidget().setText('My text content')

        # self.showGui(box.ui)

        self.assertEqual(dock1.name(), 'MyMap1')
        self.assertEqual(dock2.name(), 'MyMap2')
        self.assertEqual(dock3.name(), 'MySpeclib1')
        self.assertEqual(dock4.name(), 'MyText1')

        sources1 = dataSourceState(box)
        views1 = dataViewState(box)
        layerSources1 = sorted([l.source() for l in box.project().mapLayers().values()])
        box.actionSaveProject().trigger()

        self.assertTrue('<EnMAPBox>' in projectXml())
        box.close()
        self.assertTrue('<EnMAPBox>' in projectXml())
        QgsProject.instance().removeAllMapLayers()
        self.assertTrue('<EnMAPBox>' in projectXml())
        self.assertTrue(EnMAPBox.instance() is None)
        settings = enmapboxSettings()

        settings.setValue(EnMAPBoxSettings.STARTUP_LOAD_PROJECT, False)
        box = EnMAPBox(load_core_apps=False, load_other_apps=False)
        self.assertTrue('<EnMAPBox>' in projectXml())
        self.assertEqual(len(box.dataSources()), 0)
        self.assertEqual(len(box.docks()), 0)

        self.assertTrue('<EnMAPBox>' in projectXml())
        self.assertTrue(box.readProject(tmp_path))
        self.assertTrue('<EnMAPBox>' in projectXml())
        sources2 = dataSourceState(box)
        views2 = dataViewState(box)
        layerSources2 = sorted([lyr.source() for lyr in box.project().mapLayers().values()])
        self.showGui(box.ui)
        self.assertTrue('<EnMAPBox>' in projectXml())
        if len(sources2) == 0:
            info = ['Info EnMAP-Box DataSources']
            for ds in box.dataSources():
                info.append(f'DS: {ds}')
            info.append('Docks:')
            for dock in box.docks():
                info.append(f' {dock}')
            info.append('EnMAPBox().project():')
            info.append(box.project().debugInfo())
            info.append('QgsProject.instance():')
            for lyrID, lyr in QgsProject.instance().mapLayers():
                info.append(f'\t{lyrID}:{lyr}')
            print('\n'.join(info), file=sys.stderr)

        self.assertEqual(sources1, sources2)
        self.assertEqual(views1, views2)
        self.assertEqual(layerSources1, layerSources2)

        box.close()
        QgsProject.instance().removeAllMapLayers()
        self.assertTrue('<EnMAPBox>' in projectXml())
        # load on startup
        settings.setValue(EnMAPBoxSettings.STARTUP_LOAD_PROJECT, True)
        box = EnMAPBox(load_core_apps=False, load_other_apps=False)

        sources3 = dataSourceState(box)
        views3 = dataViewState(box)
        layerSources3 = sorted([l.source() for l in box.project().mapLayers().values()])
        self.assertEqual(sources1, sources3)
        self.assertEqual(views1, views3)
        self.assertEqual(layerSources1, layerSources3)
        self.showGui(box.ui)

        QgsProject.instance().removeAllMapLayers()
        self.assertTrue('<EnMAPBox>' in projectXml())

        QgsProject.setInstance(proj_old)
        self.assertFalse('<EnMAPBox>' in projectXml())


if __name__ == '__main__':
    unittest.main(buffer=False)
