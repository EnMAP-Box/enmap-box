# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/enmapboxintegration.py

    This file shows how to integrate your own algorithms and user interfaces into the EnMAP-Box.
    ---------------------
    Date                 : Juli 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
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
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu
from enmapbox.gui.applications import EnMAPBoxApplication
from lmuvegetationapps import APP_DIR


class SpecDeepMap(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super(SpecDeepMap, self).__init__(enmapBox, parent=parent)
        self.name = 'SpecDeepMap'
        self.version = 'Version 1'
        self.licence = 'GNU'

    def menu(self, appMenu):
        """
        Specify menu, submenus and actions
        :return: the QMenu or QAction to be added to the "Applications" menu.
        """


        appMenu = self.enmapbox.menu('Applications')

        menu = self.utilsAddMenuInAlphanumericOrder(appMenu, self.name)
        menu.setIcon(self.icon())

        a = menu.addAction('RasterSplitter')
        a.triggered.connect(self.start_GUI_IVVRM)

        b = menu.addAction('DatasetSplitter')
        b.triggered.connect(self.start_GUI_LUT)

        c = menu.addAction('DeepTrain')
        c.triggered.connect(self.start_GUI_Inv)

        d = menu.addAction('DeepInterference')
        d.triggered.connect(self.start_GUI_VIT)

        appMenu.addMenu(menu)
        return menu

    def start_GUI_IVVRM(self, *args):
        from lmuvegetationapps.IVVRM.IVVRM_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()
        # #the the EnMAP-Box know if you create any new file
        # gui1.sigFileCreated.connect(self.enmapbox.addSource)

    def start_GUI_LUT(self, *args):
        from lmuvegetationapps.LUT.CreateLUT_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()

    def start_GUI_Inv(self, *args):
        from lmuvegetationapps.LUT.InvertLUT_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()

    def start_GUI_VIT(self, *args):
        from lmuvegetationapps.VIT.VIT_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()

    def start_GUI_PWR(self, *args):
        from lmuvegetationapps.PWR.PWR_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()

    def start_GUI_ASI(self, *args):
        from lmuvegetationapps.ASI.ASI_GUI_core import MainUiFunc
        m = MainUiFunc()
        m.show()

    def start_GUI_iREIP(self, *args):
        from lmuvegetationapps.iREIP.iREIP_GUI_core import MainUiFunc
        m = MainUiFunc()
        m.show()

    def start_GUI_ProcessorInversion(self, *args):
        from lmuvegetationapps.Processor.Processor_Inversion_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()

    def start_GUI_ProcessorTraining(self, *args):
        from lmuvegetationapps.Processor.Processor_Training_GUI import MainUiFunc
        m = MainUiFunc()
        m.show()


### Interfaces to use algorithms in algorithms.py within
### QGIS Processing Framework


