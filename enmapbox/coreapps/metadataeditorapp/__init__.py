# -*- coding: utf-8 -*-

"""
***************************************************************************
    metadataeditorapp/__init__.py

    EnMAP-Box Metadata Editor
    ---------------------
    Date                 : April 2018
    Copyright            : (C) 2018 by Benjamin Jakimow
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

APP_DIR = os.path.dirname(__file__)
APP_NAME = 'Metadata Viewer'
VERSION = '0.3'
LICENSE = 'GPL-3'


class MetaDataEditorApp(EnMAPBoxApplication):
    """
    This Class inherits from an EnMAPBoxApplication
    """

    def __init__(self, enmapBox, parent=None):
        super(MetaDataEditorApp, self).__init__(enmapBox, parent=parent)

        # specify the name of this app
        self.name = APP_NAME

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
        appMenu = self.enmapbox.menu('Tools')

        a = self.utilsAddActionInAlphanumericOrder(appMenu, APP_NAME)

        assert isinstance(a, QAction)

        a.triggered.connect(self.startGUI)

        return None

    def startGUI(self):
        from metadataeditorapp.metadataeditor import MetadataEditorDialog
        d = MetadataEditorDialog(parent=self.enmapbox.ui)
        d.setEnMAPBox(self.enmapbox)
        d.show()


def enmapboxApplicationFactory(enmapBox):
    """
    Returns a list of EnMAPBoxApplications
    :param enmapBox: the EnMAP-Box instance.
    :return: EnMAPBoxApplication | [list-of-EnMAPBoxApplications]
    """
    # returns a list of EnMAP-Box Applications. Usually only one is returned,
    # but you might provide as many as you like.
    return [MetaDataEditorApp(enmapBox)]
