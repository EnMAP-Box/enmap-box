# -*- coding: utf-8 -*-

"""
***************************************************************************
    speclib/__init__.py

    EnMAP-Box Spectral Mixer
    ---------------------
    Date                 : August 2020
    Copyright            : (C) 2020 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import typing
import pathlib

from qgis.core import QgsVectorLayer

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.gui import SpectralLibrary
from enmapbox.gui.dataviews.docks import SpectralLibraryDock

APP_DIR = pathlib.Path(__file__).parent
APP_NAME = 'Spectral Mixer'
VERSION = '0.1'
LICENSE = 'GPL-3'


class SpecMixApp(EnMAPBoxApplication):
    """
    This Class inherits from an EnMAPBoxApplication
    """

    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        # specify the name of this app
        self.name = APP_NAME
        self.mWidgets = []
        # specify a version string

        self.version = VERSION

        # specify a licence under which you distribute this application
        self.licence = LICENSE

    def icon(self):
        """
        This function returns the QIcon of your Application
        :return: QIcon()
        """
        return QIcon(':/enmapbox/gui/ui/icons/enmapbox.svg')

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
        appMenu = self.enmapbox.menu('Applications')

        a = appMenu.addAction(APP_NAME)

        assert isinstance(a, QAction)

        a.triggered.connect(self.startGUI)

        return None

    def startGUI(self):
        from specmixapp.specmix import SpecMixWidget
        w = SpecMixWidget()
        self.enmapbox.sigSpectralLibraryAdded[QgsVectorLayer].connect(w.addSpectralLibraries)
        self.enmapbox.sigSpectralLibraryRemoved[QgsVectorLayer].connect(w.removeSpectralLibraries)

        existing: typing.List[SpectralLibrary] = list()
        for dw in self.enmapbox.docks(SpectralLibraryDock):
            if isinstance(dw, SpectralLibraryDock):
                existing.append(dw.speclib())
        w.addSpectralLibraries(existing)
        w.show()
        self.mWidgets.append(w)


def enmapboxApplicationFactory(enmapBox):
    """
    Returns a list of EnMAPBoxApplications
    :param enmapBox: the EnMAP-Box instance.
    :return: EnMAPBoxApplication | [list-of-EnMAPBoxApplications]
    """
    # returns a list of EnMAP-Box Applications. Usually only one is returned,
    # but you might provide as many as you like.
    #
    return []  # disabled until fixed
    return [SpecMixApp(enmapBox)]
