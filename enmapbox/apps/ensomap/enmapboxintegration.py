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
"""

import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction
from enmapbox.gui.applications import EnMAPBoxApplication

from ensomap import APP_DIR

import sys
sys.path.insert(0, APP_DIR)
import hys
# from ensomap_ui import ENSOMAP_UI

from PyQt5.QtCore    import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui     import *

import numpy as np
import time
import hys
import csv

from hys.ui_map import *
from hys.ui_msk import *
from hys.ui_cal import *
from hys.ui_val import *

class ENSOMAP_UI(ui_map, ui_msk, ui_cal, ui_val, QWidget):

    def __init__(self, dname, parent=None):
        super(ENSOMAP_UI, self).__init__(parent=parent)
        
        self.app_name = "ENSOMAP"
        self.app_version = hys.__version__

        # =========================================================================================
        # CREATE THE BASE
        self.gui = hys.WIDGET(self, self.app_name + " - " + self.app_version)

        # =========================================================================================
        # CREATE THE BASE TAB
        self.gui.widget_tab()

        self.insert_map(dname)
        self.insert_msk(dname)
        self.insert_cal(dname)
        self.insert_val(dname)

        
        self.gui.widget_tab_close()

        # =========================================================================================
        # CREATE THE LINE WITH BUTTON
        self.gui.widget_add_spacing(10)
        self.gui.widget_row_framed(alignment=Qt.AlignLeft, style = QFrame.StyledPanel | QFrame.Raised)
        self.gui.widget_push_button('Close', action=self.quit)
        self.gui.widget_row_framed_close()


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def quit(self):
        self.close()


class EnSoMAP(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):
        super(EnSoMAP, self).__init__(enmapBox, parent=parent)
        self.name = 'EnSoMAP'
        self.version = '2.0'
        self.licence = 'TBD'
    
    def icon(self):
        pathIcon = os.path.join(APP_DIR, 'icon.png')
        return QIcon(pathIcon)

    def menu(self, appMenu):
        appMenu = self.enmapbox.menu('Applications')
        menu = appMenu.addMenu('Soil Applications')
        menu.setIcon(self.icon())
        a = menu.addAction('EnSoMAP 2.0')
        a.triggered.connect(self.startGUI)
        appMenu.addMenu(menu)
        return menu
    
    def startGUI(self, *args):
        homedir = os.path.expanduser('~')
        w = ENSOMAP_UI(homedir)
        w.show()
        w.center()
        