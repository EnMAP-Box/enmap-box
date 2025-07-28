# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

import os

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'
__date__ = '2017-07-17'
__copyright__ = 'Copyright 2017, Benjamin Jakimow'

import unittest

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.applications import EnMAPBoxApplication

from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.core import QgsProject

start_app()


def has_package(name: str):
    try:
        __import__(name)
        return True
    except (ModuleNotFoundError, SystemError):
        return False


has_numba = has_package('numba')
has_hys = has_package('hys')


class test_ensomap(EnMAPBoxTestCase):

    @unittest.skipIf(not has_hys, 'hys package not installed')
    def test_imports(self):
        import ensomap
        self.assertTrue(os.path.isfile(ensomap.__file__))
        import hys

        self.assertTrue(os.path.isfile(hys.__file__))

    @unittest.skipIf(not has_numba, 'numba not installed')
    def test_EnSOMAP_App(self):
        emb = EnMAPBox(load_core_apps=False, load_other_apps=False)

        from ensomap import enmapboxApplicationFactory

        app = enmapboxApplicationFactory(emb)

        self.assertTrue(isinstance(app, list) or isinstance(app, EnMAPBoxApplication))
        emb.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == "__main__":
    unittest.main(buffer=False)
