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
from enmapbox import initPythonPaths
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase

initPythonPaths()

try:
    from enpt_enmapboxapp.enpt_enmapboxapp import EnPTEnMAPBoxApp
except ModuleNotFoundError as ex:
    if ex.name == 'enpt_enmapboxapp':
        raise unittest.SkipTest('Missing enpt_enmapboxapp module. Skip tests')
    else:
        raise ex


class EnPTTestCases(EnMAPBoxTestCase):

    def test_application(self):
        EB = EnMAPBox()

        app = [a for a in EB.applicationRegistry.applications() if isinstance(a, EnPTEnMAPBoxApp)]
        self.assertTrue(len(app) == 1, msg='EnPTEnMAPBoxApp was not loaded during EnMAP-Box startup')

        app = app[0]
        self.assertIsInstance(app, EnPTEnMAPBoxApp)
        # app.startGUI()
        self.showGui(EB.ui)


if __name__ == "__main__":
    unittest.main(buffer=False)
