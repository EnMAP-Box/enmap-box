# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    EnMAPBoxPlugin.py
    ---------------------
    Date                 : August 2017
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
import sys
import typing

from qgis.PyQt.QtCore import QOperatingSystemVersion
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis
from qgis.gui import QgisInterface, QgsDockWidget


class EnMAPBoxPlugin(object):

    def __init__(self, *args, **kwds):
        # make site-packages available to python
        self.enmapBox = None
        self.pluginToolbarActions: typing.List[QAction] = []
        self.rasterMenuActions: typing.List[QAction] = []
        self.dockWidgets: typing.List[QgsDockWidget] = []

        if QOperatingSystemVersion.current().name() == 'macOS':
            # os.environ['SKLEARN_SITE_JOBLIB']='True'True
            # fix for issue #221
            os.environ['JOBLIB_MULTIPROCESSING'] = '0'

        pathes = sys.path[:]

        import enmapbox
        enmapbox.initPythonPaths()
        # run a minimum dependency check
        self.initialDependencyCheck()

        # initialize resources, processing provider etc.
        enmapbox.initAll()

        self.mAddedSysPaths = [p for p in sys.path if p not in pathes]

    def initialDependencyCheck(self):
        """
        Runs a check for availability of package dependencies and summarized error messages
        :return:
        """
        from enmapbox import messageLog
        from enmapbox.dependencycheck import missingPackageInfo, requiredPackages
        missing = [p for p in requiredPackages() if not p.isInstalled()]
        if len(missing) > 0:
            info = missingPackageInfo(missing, html=False)
            # warnings.warn(info, ImportWarning)
            messageLog(info, level=Qgis.Warning)

    def initGui(self):

        import enmapbox
        from qgis.utils import iface
        if isinstance(iface, QgisInterface):

            actionStartBox = QAction(enmapbox.icon(), 'EnMAP-Box', iface)
            actionStartBox.triggered.connect(self.run)
            actionAbout = QAction(QIcon(':/enmapbox/gui/ui/icons/metadata.svg'),
                                  'About')
            actionAbout.triggered.connect(self.showAboutDialog)
            self.rasterMenuActions.append(actionStartBox)
            self.rasterMenuActions.append(actionAbout)
            self.pluginToolbarActions.append(actionStartBox)

            for action in self.rasterMenuActions:
                iface.addPluginToRasterMenu('EnMAP-Box', action)

            for action in self.pluginToolbarActions:
                iface.addToolBarIcon(action)

            # init stand-alone apps, that can operate in QGIS GUI without EnMAP-Box
            self.initStandAloneAppGuis()

        else:
            print('EnMAPBoxPlugin.initGui() called without iface')

    def showAboutDialog(self):
        from enmapbox.gui.about import AboutDialog
        d = AboutDialog()
        d.exec()

    def initProcessing(self):
        """
        Init enmapbox for processing provider only
        :return:
        :rtype:
        """
        import enmapbox
        enmapbox.initPythonPaths()

    def run(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()
        if not isinstance(self.enmapBox, EnMAPBox):
            self.enmapBox = EnMAPBox()
            assert self.enmapBox == EnMAPBox.instance()
            self.enmapBox.run()
        else:
            self.enmapBox.ui.show()

    def unload(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        from qgis.utils import iface
        if isinstance(iface, QgisInterface):

            for action in self.pluginToolbarActions:
                iface.removeToolBarIcon(action)

            for action in self.rasterMenuActions:
                iface.removePluginRasterMenu('EnMAP-Box', action)

            for dockWidget in self.dockWidgets:
                iface.removeDockWidget(dockWidget)

        import enmapbox
        enmapbox.unloadAll()

        if isinstance(EnMAPBox.instance(), EnMAPBox):
            EnMAPBox.instance().close()
        EnMAPBox._instance = None

    def initStandAloneAppGuis(self):
        """
        We started to move external QGIS Plugins into the EnMAP-Box as applications.
        E.g. the GEE Time Series Explorer plugin.
        Those apps can now be used inside the EnMAP-Box GUI, but also in QGIS GUI as stand-alone.
        Therefore, we need to add toolbar icons.
        Note that an app can't do this on it's own, because apps only get initialized on box startup.
        """

        self.initGeeTimeseriesExplorerGui()

    def initGeeTimeseriesExplorerGui(self):
        from qgis.utils import iface
        from geetimeseriesexplorerapp import GeeTimeseriesExplorerApp

        self.geeTimeseriesExplorerApp = GeeTimeseriesExplorerApp(None, iface)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.geeTimeseriesExplorerApp.actionToggleMainDock)
        self.pluginToolbarActions.append(self.geeTimeseriesExplorerApp.actionCurrentLocationMapTool)
        self.dockWidgets.append(self.geeTimeseriesExplorerApp.mainDock)
        self.dockWidgets.append(self.geeTimeseriesExplorerApp.profileDock)
