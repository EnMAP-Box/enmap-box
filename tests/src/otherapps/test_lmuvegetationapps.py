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

from enmapbox import EnMAPBox, initPythonPaths
from enmapbox.testing import EnMAPBoxTestCase

initPythonPaths()


class test_applications(EnMAPBoxTestCase):

    def test_MainUiFunc(self):
        from lmuapps.lmuvegetationapps.IVVRM.IVVRM_GUI import MainUiFunc

        m = MainUiFunc()
        self.showGui(m)

    def test_application(self):
        EB = EnMAPBox.instance()
        if EB is None:
            EB = EnMAPBox()
        EB.ui.hide()

        from lmuapps.lmuvegetationapps.IVVRM.IVVRM_GUI import IVVRM_GUI

        w = IVVRM_GUI()
        self.showGui(w)
        # app = LMU_EnMAPBoxApp(EB)
        # app.start_GUI_IVVRM()

        self.showGui(EB.ui)


if __name__ == "__main__":
    unittest.main(buffer=False)
