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

from PyQt5.QtWidgets import QWidget

import enmapboxtestdata
from enmapbox.apps.lmuvegetationapps.IVVRM.IVVRM_GUI import IVVRM_GUI, MainUiFunc
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase, start_app
from lmuvegetationapps.IVVRM.IVVRM_GUI import SensorEditor

start_app()

def has_package(name: str):
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False


class test_applications(EnMAPBoxTestCase):

    def test_IVVRM(self):
        m = MainUiFunc()

        self.showGui(m.ivvrm.gui)

    def test_SensorEditor(self):
        m = MainUiFunc()
        editor: SensorEditor = m.sensoreditor
        cb = m.sensoreditor.gui.mLayer
        self.assertEqual(cb.count(), 0)

        editor.open_image(input=enmapboxtestdata.enmap_potsdam)
        # editor.open_image()
        # editor.image_read()
        # editor.check_flags()


        self.assertEqual(cb.count(), 1)
        self.showGui(m.sensoreditor.gui)

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
