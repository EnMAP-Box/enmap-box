# -*- coding: utf-8 -*-
"""
***************************************************************************
    test_enmapbox.py
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

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.core import QgsProject

start_app()


class EnMAPBoxTests(EnMAPBoxTestCase):

    def test_addSources(self):
        E = EnMAPBox(load_core_apps=False, load_other_apps=False)

        if True:
            whitelist = ['profileanalyticsapp']
            E.initEnMAPBoxApplications(load_core_apps=True, load_other_apps=True,
                                       whitelist=whitelist)
            appNames = [a.name for a in E.applicationRegistry.applications()]
            self.assertListEqual(['ProfileAnalyticsApp'], appNames)
        if False:
            blacklist = ['profileanalyticsapp']
            E.initEnMAPBoxApplications(load_core_apps=True, load_other_apps=True,
                                       blacklist=blacklist)

            appNames = [a.name for a in E.applicationRegistry.applications()]
            self.assertTrue('ProfileAnalyticsApp' not in appNames)

        E.loadExampleData()
        # sl = TestObjects.createSpectralLibrary()
        # E.createSpectralLibraryDock(speclib=sl, name='Test')

        E.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
