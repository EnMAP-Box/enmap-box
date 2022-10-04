# -*- coding: utf-8 -*-
"""
***************************************************************************
    test_enMAPBox
    ---------------------
    Date                 : April 2018
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

import pathlib
import site
import unittest

from enmapbox import DIR_REPO
from enmapbox.testing import TestCase
from qgis.utils import iface


class TestEnMAPBoxPlugin(TestCase):
    deploy_folder = pathlib.Path(DIR_REPO) / 'deploy'

    def test_metadata(self):
        from qgis.utils import findPlugins

        path_repo_root = pathlib.Path(DIR_REPO).parent
        plugins = {k: parser for k, parser in findPlugins(path_repo_root.as_posix())}

        self.assertTrue('enmap-box' in plugins.keys(), msg=f'Unable to find enmap-box below {path_repo_root}')
        parser = plugins['enmap-box']

        # details in
        # https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#plugin-metadata
        self.assertTrue(parser.get('general', 'name') != '')
        self.assertTrue(parser.get('general', 'qgisMinimumVersion') != '')
        self.assertTrue(parser.get('general', 'description') != '')
        self.assertTrue(parser.get('general', 'about') != '')
        self.assertTrue(parser.get('general', 'version') != '')
        self.assertTrue(parser.get('general', 'author') != '')
        self.assertTrue(parser.get('general', 'email') != '')
        self.assertTrue(parser.get('general', 'repository') != '')

    def test_loadplugin(self):
        from enmapbox.enmapboxplugin import EnMAPBoxPlugin

        plugin = EnMAPBoxPlugin(iface)
        self.assertIsInstance(plugin, EnMAPBoxPlugin)
        plugin.initGui()
        plugin.unload()

    @unittest.skipIf(not deploy_folder.is_dir(), 'Missing deploy folder')
    def test_loadplugin2(self):
        import qgis.utils
        name = 'enmapboxplugin'
        site.addsitedir(self.deploy_folder)
        self.assertTrue(qgis.utils.loadPlugin(name))
        self.assertTrue(qgis.utils.startPlugin(name))

    def test_dependencies(self):
        from enmapbox.dependencycheck import requiredPackages, missingPackages, missingPackageInfo, PIPPackage

        pkgs = requiredPackages()
        for p in pkgs:
            self.assertIsInstance(p, PIPPackage)

        missing = missingPackages()
        self.assertIsInstance(missing, list)
        missing += [PIPPackage('foobar42')]

        info = missingPackageInfo(missing)
        self.assertIsInstance(info, str)
        self.assertTrue('foobar42' in info)
        from enmapbox.enmapboxplugin import EnMAPBoxPlugin

        import qgis.utils
        p = EnMAPBoxPlugin(qgis.utils.iface)
        p.initialDependencyCheck()


if __name__ == '__main__':
    unittest.main(buffer=False)
