# -*- coding: utf-8 -*-

"""
***************************************************************************
    hubtimeseriesviewer/__init__.py

    Package definition of HUB TimeSeriesViewer for EnMAP-Box
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

import importlib
import os

import qgis.utils
from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox

APP_DIR = os.path.dirname(__file__)


def qgisPluginInstalled() -> bool:
    """
    Returns True if the EO Time Series Viewer QGIS Plugin is installed
    :return: bool
    """
    qgis.utils.updateAvailablePlugins()
    return importlib.util.find_spec('eotimeseriesviewer') is not None


class EOTimeSeriesViewerApp(EnMAPBoxApplication):

    def __init__(self, enmapBox, parent=None):

        super(EOTimeSeriesViewerApp, self).__init__(enmapBox, parent=parent)
        self.mPluginInstalled = qgisPluginInstalled()

        self.name = 'EO Time Series Viewer'
        self.mTSVInstance = None

        if self.mPluginInstalled:
            import eotimeseriesviewer
            self.version = eotimeseriesviewer.__version__
            self.licence = 'GNU GPL-3'
        else:
            self.version = 'Unknown'
            self.licence = 'Unknown'
        self.mTSVInstance = None

    def icon(self):
        if self.mPluginInstalled:
            import eotimeseriesviewer
            return eotimeseriesviewer.icon()
        else:
            return QIcon()

    def menu(self, appMenu):
        a = self.utilsAddActionInAlphanumericOrder(appMenu, self.name)
        a.setIcon(self.icon())
        a.triggered.connect(self.startGUI)
        return a

    def startGUI(self, *args):
        if qgisPluginInstalled():
            from eotimeseriesviewer.main import TimeSeriesViewer

            if not isinstance(self.mTSVInstance, TimeSeriesViewer):
                self.mTSVInstance = TimeSeriesViewer.instance()
                if not isinstance(self.mTSVInstance, TimeSeriesViewer):
                    self.mTSVInstance = TimeSeriesViewer()
                    self.mTSVInstance.ui.sigAboutToBeClosed.connect(self.onTimeSeriesViewerClosed)

            self.mTSVInstance.show()

        else:
            QMessageBox.information(None, 'Missing QGIS Plugin',
                                    'Please install and activate the EO Time Series Viewer QGIS Plugin.')

    def onTimeSeriesViewerClosed(self, *args, **kwds):
        self.mTSVInstance = None


def enmapboxApplicationFactory(enmapBox):
    """
    Returns a list of EnMAPBoxApplications
    :param enmapBox: the EnMAP-Box instance.
    :return: [list-of-EnMAPBoxApplications]
    """

    return [EOTimeSeriesViewerApp(enmapBox)]
