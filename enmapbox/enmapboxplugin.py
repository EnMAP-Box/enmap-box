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
from os.path import basename, splitext
from typing import List

from enmapbox.dependencycheck import missingTestData, installTestData, PIPPackage
from enmapbox.enmapboxprojectsettings import EnMAPBoxProjectSettings
from qgis.PyQt.QtCore import QOperatingSystemVersion, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject, Qgis
from qgis.gui import QgisInterface, QgsDockWidget


class EnMAPBoxPlugin(object):

    def __init__(self, *args, **kwds):
        # make site-packages available to python
        self.enmapBox = None
        self.pluginToolbarActions: List[QAction] = []
        self.rasterMenuActions: List[QAction] = []
        self.dockWidgets: List[QgsDockWidget] = []
        self.mMissingCoreRequirements: List[PIPPackage] = []

        if QOperatingSystemVersion.current().name() == 'macOS':
            # os.environ['SKLEARN_SITE_JOBLIB']='True'
            # fix for issue #221
            os.environ['JOBLIB_MULTIPROCESSING'] = '0'

        pathes = sys.path[:]

        import enmapbox
        enmapbox.initPythonPaths()

        # run a minimum dependency check
        missing = self.initialDependencyCheck()
        self.mMissingCoreRequirements.extend(missing)

        # initialize resources, processing provider etc.
        if self.corePackagesAvailable():
            enmapbox.initAll()
            self.mAddedSysPaths = [p for p in sys.path if p not in pathes]

            # listen out for project save/restore, and update our state accordingly
            # (adopted from Data Plotly plugin)
            QgsProject.instance().writeProject.connect(self.writeProject)
            QgsProject.instance().readProject.connect(self.readProject)

    def corePackagesAvailable(self) -> bool:
        """
        Returns True if all core packages are available
        to provide basic EnMAP-Box functionality
        :return: bool
        """
        return len(self.mMissingCoreRequirements) == 0

    def writeProject(self, document: QDomDocument):
        settings = EnMAPBoxProjectSettings()
        settings.writeToProject(document)

    def readProject(self, document: QDomDocument):
        settings = EnMAPBoxProjectSettings()
        settings.readFromProject(document)

    def initialDependencyCheck(self) -> List[PIPPackage]:
        """
        Runs a check for availability of package dependencies and summarized error messages
        Returns a list of missing core requirements without which the EnMAP-Box
        cannot function properly.
        :return:
        """
        from enmapbox import messageLog
        from enmapbox.dependencycheck import missingPackageInfo, requiredPackages
        missing = [p for p in requiredPackages() if p.isCoreRequirement() and not p.isInstalled()]
        if len(missing) > 0:
            info = missingPackageInfo(missing, html=False)
            # warnings.warn(info, ImportWarning)
            messageLog(info, level=Qgis.MessageLevel.Warning)
        return missing

    def initGui(self):
        from qgis.utils import iface
        import enmapbox

        actionStartBox = QAction(enmapbox.icon(), 'EnMAP-Box', iface)
        actionAbout = QAction(QIcon(':/enmapbox/gui/ui/icons/metadata.svg'), 'About')

        if not self.corePackagesAvailable():
            def show_message_box(*args, **kwargs):
                mbox = QMessageBox()
                mbox.setWindowTitle('Missing Packages')
                mbox.setTextFormat(Qt.TextFormat.RichText)
                info = self.missingPackageInfos(self.mMissingCoreRequirements)
                mbox.setText(info)
                mbox.exec()

            actionStartBox.triggered.connect(show_message_box)
            actionAbout.triggered.connect(self.showAboutDialog)

            self.rasterMenuActions.append(actionStartBox)
            self.rasterMenuActions.append(actionAbout)
            self.pluginToolbarActions.append(actionStartBox)

            self._add_actions()
            return

        actionStartBox.triggered.connect(self.run)
        actionAbout.triggered.connect(self.showAboutDialog)

        actionAddExampleData = QAction(QIcon(), 'Add Example Data')
        actionAddExampleData.triggered.connect(self.addExampleData)

        self.rasterMenuActions.append(actionStartBox)
        self.rasterMenuActions.append(actionAddExampleData)
        self.rasterMenuActions.append(actionAbout)
        self.pluginToolbarActions.append(actionStartBox)

        self._add_actions()

        # init stand-alone apps, that can operate in QGIS GUI without EnMAP-Box
        self.initStandAloneAppGuis()

    def _add_actions(self):
        """
        Add actions to QGIS GUI
        """
        from qgis.utils import iface
        for action in self.rasterMenuActions:
            iface.addPluginToRasterMenu('EnMAP-Box', action)

        for action in self.pluginToolbarActions:
            iface.addToolBarIcon(action)

    def _remove_actions(self):
        """
        Remove actions from QGIS GUI
        """
        from qgis.utils import iface
        if isinstance(iface, QgisInterface):
            for action in self.pluginToolbarActions:
                iface.removeToolBarIcon(action)

            for action in self.rasterMenuActions:
                iface.removePluginRasterMenu('EnMAP-Box', action)

            for dockWidget in self.dockWidgets:
                iface.removeDockWidget(dockWidget)

    @staticmethod
    def missingPackageInfos(missing_packages: List[PIPPackage], cli: bool = False) -> str:

        if cli:
            info = 'Missing python package(s).\nPlease install: '
            for i, p in enumerate(missing_packages):
                info += f'\n{i + 1}: {p.pipPkgName}'
                if p.comment:
                    info += f' - {p.comment}'

            info += '\n Please visit https://enmap-box.readthedocs.io for advice.'
        else:
            # for GUI message dialog
            info = ('<b>The EnMAP-Box is installed! &#x1F389;</b><br>'
                    'To launch the basic EnMAP-Box, you just need to install a few remaining Python dependencies:<br>')

            for i, p in enumerate(missing_packages):
                info += f'<br>{i + 1}: {p.pipPkgName}'
                if p.comment and len(p.comment) > 0:
                    info += f' - {p.comment}'

            info += ('<br><br>'  # <i>How to fix this:</i>'
                     # '<ol style="margin-left: 0px;"><li>Open your terminal/command prompt and run:'
                     # '<br><code>pip install &lt;missing packages&gt;</code>'
                     # '<br>(or <code>conda install &lt;missing packages&gt;</code>)</li>'
                     # '<li>Restart QGIS</li>'
                     # '</ol>'
                     # 'Other EnMAP-Box features may require additional Python packages. '
                     'To fix this, please follow the '
                     '<a href="https://enmap-box.readthedocs.io/en/latest/usr_section/usr_installation.html">'
                     'EnMAP-Box installation guide</a>.'

                     )
        return info

    def showAboutDialog(self):
        from enmapbox.gui.about import AboutDialog
        d = AboutDialog()
        d.exec()

    def addExampleData(self):

        if missingTestData():
            installTestData()

        from enmapbox.exampledata import hires, enmap, landcover_point, landcover_polygon

        layers = [
            QgsVectorLayer(landcover_polygon, splitext(basename(landcover_polygon))[0]),
            QgsVectorLayer(landcover_point, splitext(basename(landcover_point))[0]),
            QgsRasterLayer(hires, splitext(basename(hires))[0]),
            QgsRasterLayer(enmap, splitext(basename(enmap))[0])
        ]

        QgsProject.instance().addMapLayers(layers)

    def initProcessing(self):
        """
        Init enmapbox for processing provider only
        :return:
        :rtype:
        """
        if not self.corePackagesAvailable():
            info = self.missingPackageInfos(self.mMissingCoreRequirements, cli=True)
            raise ModuleNotFoundError(info)

        import enmapbox
        enmapbox.initPythonPaths()

    def run(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()
        if not isinstance(self.enmapBox, EnMAPBox):
            self.enmapBox = EnMAPBox()
            if self.enmapBox != EnMAPBox.instance():
                raise RuntimeError("EnMAPBox singleton initialization failed")
            self.enmapBox.run()
        else:
            self.enmapBox.ui.show()

    def unload(self):
        self._remove_actions()

        if not self.corePackagesAvailable():
            return

        from enmapbox.gui.enmapboxgui import EnMAPBox

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
        Note that an app can't do this on its own, because apps only get initialized on box startup.
        """

        self.initCurrentLocationMapTool()

        # here we are adding all the EO4Q apps manually, later we should do that automatically
        self.initGeeTimeseriesExplorerGui()
        self.initLocationBrowserGui()
        self.initProfileAnalyticsGui()
        self.initRasterBandStackingGui()
        self.initSensorProductImportGui()
        self.initSpectralIndexExplorerGui()
        self.initTemporalRasterStackControllerGui()

    def initCurrentLocationMapTool(self):
        """
        This map tool can be used by all stand-alone apps, that need to select a location inside the QGIS map canvas.
        """
        from qgis.utils import iface
        from geetimeseriesexplorerapp import MapTool

        self.actionCurrentLocationMapTool = QAction(
            QIcon(':/qps/ui/icons/select_location.svg'), 'Select Current Location'
        )
        self.actionCurrentLocationMapTool.setCheckable(True)
        iface.addToolBarIcon(self.actionCurrentLocationMapTool)
        self.actionCurrentLocationMapTool.toggled.connect(self.onCurrentLocationMapToolClicked)
        self.currentLocationMapTool = MapTool(iface.mapCanvas(), self.actionCurrentLocationMapTool)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.actionCurrentLocationMapTool)

    def onCurrentLocationMapToolClicked(self):
        from qgis.utils import iface
        if self.actionCurrentLocationMapTool.isChecked():
            iface.mapCanvas().setMapTool(self.currentLocationMapTool)
        else:
            iface.mapCanvas().unsetMapTool(self.currentLocationMapTool)

    def initGeeTimeseriesExplorerGui(self):
        from qgis.utils import iface
        from geetimeseriesexplorerapp import GeeTimeseriesExplorerApp

        self.geeTimeseriesExplorerApp = GeeTimeseriesExplorerApp(None, iface, self.currentLocationMapTool)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.geeTimeseriesExplorerApp.actionToggleMainDock)
        self.dockWidgets.append(self.geeTimeseriesExplorerApp.mainDock)
        self.dockWidgets.append(self.geeTimeseriesExplorerApp.profileDock)

    def initProfileAnalyticsGui(self):
        from qgis.utils import iface
        from profileanalyticsapp import ProfileAnalyticsApp

        self.profileAnalyticsApp = ProfileAnalyticsApp(None, iface, self.currentLocationMapTool)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.profileAnalyticsApp.actionToggleDock)
        self.dockWidgets.append(self.profileAnalyticsApp.dock)

    def initLocationBrowserGui(self):
        from qgis.utils import iface
        from locationbrowserapp import LocationBrowserApp

        self.locationBrowserApp = LocationBrowserApp(None, iface, self.currentLocationMapTool)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.locationBrowserApp.actionToggleDock)
        self.dockWidgets.append(self.locationBrowserApp.dock)

    def initRasterBandStackingGui(self):
        from qgis.utils import iface
        from rasterbandstackingapp import RasterBandStackingApp

        self.rasterBandStackingApp = RasterBandStackingApp(None, iface, self.currentLocationMapTool)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.rasterBandStackingApp.actionToggleDock)
        self.dockWidgets.append(self.rasterBandStackingApp.dock)

    def initRasterMaskingGui(self):
        from qgis.utils import iface
        from rastermaskingapp import RasterMaskingApp

        self.rasterMaskingApp = RasterMaskingApp(None, iface)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.rasterMaskingApp.actionToggleDock)
        self.dockWidgets.append(self.rasterMaskingApp.dock)

    def initSensorProductImportGui(self):
        from qgis.utils import iface
        from sensorproductimportapp import SensorProductImportApp

        self.sensorProductImportApp = SensorProductImportApp(None, iface)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.sensorProductImportApp.actionToggleDock)
        self.dockWidgets.append(self.sensorProductImportApp.dock)

    def initSpectralIndexExplorerGui(self):
        from qgis.utils import iface
        from spectralindexexplorerapp import SpectralIndexExplorerApp

        self.spectralIndexExplorApp = SpectralIndexExplorerApp(None, iface)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.spectralIndexExplorApp.actionToggleDock)
        self.dockWidgets.append(self.spectralIndexExplorApp.dock)

    def initTemporalRasterStackControllerGui(self):
        from temporalrasterstackcontrollerapp import TemporalRasterStackControllerApp

        self.temporalRasterStackControllerApp = TemporalRasterStackControllerApp(None)

        # add items to be removed when unload the plugin
        self.pluginToolbarActions.append(self.temporalRasterStackControllerApp.actionToolbarIcon)
