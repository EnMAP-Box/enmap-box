# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/enmapboxintegration.py

    This module defines the interactions between an application and
    the EnMAPBox.
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

Changelog
EnGeoMAP Version 3.2
Date: February 2023
Author: Helge L. C. Daempfling
Email: hdaemp@gfz-potsdam.de

See algorithms.py and engeomap_aux_funcul.py

"""

import os
from qgis.PyQt.QtGui import QIcon
from enmapbox.gui.applications import EnMAPBoxApplication
from engeomap import APP_DIR


class EnGeoMAP(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):
        super(EnGeoMAP, self).__init__(enmapBox, parent=parent)
        self.name = 'My EnMAPBox App'
        self.version = 'Version 0.8.15'
        self.licence = 'BSD-3'

    def icon(self):
        pathIcon = os.path.join(APP_DIR, 'icon.png')
        return QIcon(pathIcon)

    def menu(self, appMenu):
        appMenu = self.enmapbox.menu('Applications')
        menu = self.utilsAddMenuInAlphanumericOrder(appMenu, 'Mineral Applications')
        menu.setIcon(self.icon())
        # add a QAction that starts your GUI
        a = menu.addAction('EnGeoMAP 3.2')
        a.triggered.connect(self.startGUI)
        return menu

    def startGUI(self, *args):
        from engeomap.userinterfaces import EnGeoMAPGUI
        ui = EnGeoMAPGUI(self.enmapbox.ui)
        ui.show()
