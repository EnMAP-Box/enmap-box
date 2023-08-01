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

from enmapbox.apps.lmuvegetationapps.IVVRM.IVVRM_GUI import IVVRM_GUI, MainUiFunc
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase


def has_package(name: str):
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False


class test_applications(EnMAPBoxTestCase):

    @unittest.skipIf(not has_package('scipy'), 'scipy is not installed')
    def test_MainUiFunc(self):
        m = MainUiFunc()
        self.showGui(m)

    @unittest.skipIf(not has_package('scipy'), 'scipy is not installed')
    def test_application(self):
        EB = EnMAPBox.instance()
        if EB is None:
            EB = EnMAPBox()
        EB.ui.hide()

        w = IVVRM_GUI()
        self.showGui(w)
        # app = LMU_EnMAPBoxApp(EB)
        # app.start_GUI_IVVRM()

        self.showGui(EB.ui)


if __name__ == "__main__":
    unittest.main(buffer=False)
