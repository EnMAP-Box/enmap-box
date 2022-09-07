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

from exampleapp import APP_DIR

from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu


class ExampleEnMAPBoxApp(EnMAPBoxApplication):
    """
    This Class derived from an EnMAPBoxApplication.

    """

    def __init__(self, enmapBox, parent=None):
        super(ExampleEnMAPBoxApp, self).__init__(enmapBox, parent=parent)

        # specify the name of this app
        self.name = 'My EnMAPBox App'

        # specify a version string
        from exampleapp import VERSION
        self.version = VERSION

        # specify a licence under which you distribute this application
        self.licence = 'BSD-3'

    def icon(self):
        """
        This function returns a QIcon of your Application
        :return:
        """
        pathIcon = os.path.join(APP_DIR, 'icon.png')
        return QIcon(pathIcon)

    def menu(self, appMenu):
        """
        Returns a QMenu that will be added to the parent `appMenu`
        :param appMenu:
        :return: QMenu
        """
        assert isinstance(appMenu, QMenu)
        """
        Specify menu, submenus and actions that become accessible from the EnMAP-Box GUI
        :return: the QMenu or QAction to be added to the "Applications" menu.
        """

        # this way you can add your QMenu/QAction to an other menu entry, e.g. 'Tools'
        # appMenu = self.enmapbox.menu('Tools')

        menu = appMenu.addMenu('Example App')
        menu.setIcon(self.icon())

        # add a QAction that starts a process of your application.
        # In this case it will open your GUI.
        a = menu.addAction('Show ExampleApp GUI')
        a.triggered.connect(self.startGUI)

        appMenu.addMenu(menu)

        return menu

    def geoAlgorithms(self):
        """
        This function returns the QGIS Processing Framework GeoAlgorithms specified by your application
        :return: [list-of-GeoAlgorithms]
        """
        # return [] #remove this line to load geoAlgorithms
        from algorithms import MyEnMAPBoxAppProcessingAlgorithm
        return [MyEnMAPBoxAppProcessingAlgorithm()]

    def startGUI(self, *args):
        from exampleapp.userinterfaces import ExampleGUI
        ui = ExampleGUI(self.enmapbox.ui)
        ui.show()
