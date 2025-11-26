# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'danschef@gfz.de'
__date__ = '2025-11-25'
__copyright__ = 'Copyright 2025, Daniel Scheffler'

import unittest
from enmapbox import initPythonPaths
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase

initPythonPaths()

try:
    from enfrosp_enmapboxapp.enfrosp_enmapboxapp import EnFROSPEnMAPBoxApp
except ModuleNotFoundError as ex:
    if ex.name == 'enfrosp_enmapboxapp':
        raise unittest.SkipTest('Missing enfrosp_enmapboxapp module. Skip tests')
    else:
        raise ex


class EnFROSPTestCases(EnMAPBoxTestCase):

    def test_application(self):
        EB = EnMAPBox()

        app = [a for a in EB.applicationRegistry.applications() if isinstance(a, EnFROSPEnMAPBoxApp)]
        self.assertTrue(len(app) == 1, msg='EnFROSPEnMAPBoxApp was not loaded during EnMAP-Box startup')

        app = app[0]
        self.assertIsInstance(app, EnFROSPEnMAPBoxApp)
        # app.startGUI()
        self.showGui(EB.ui)


if __name__ == "__main__":
    unittest.main(buffer=False)
