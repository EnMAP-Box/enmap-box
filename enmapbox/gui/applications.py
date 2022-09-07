# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    applications.py
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
import collections
import importlib
import inspect
import os
import pathlib
import re
import site
import sys
import traceback
import typing
from typing import Optional

from enmapbox import messageLog
from enmapbox.algorithmprovider import EnMAPBoxProcessingProvider
from enmapbox.gui.enmapboxgui import EnMAPBox
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsProcessingAlgorithm
from qgis.gui import QgisInterface

DEBUG = False  # set this on True to not hide external-app errors


class EnMAPBoxApplication(QObject):
    """
    Base class to describe components of an EnMAPBoxApplication
    and to provide interfaces the main EnMAP-Box
    """

    @staticmethod
    def checkRequirements(enmapBoxApp) -> (bool, str):
        """
        Tests if the EnMAPBoxApplication defines all required information.
        :param enmapBoxApp: EnMAPBoxApplication
        :return: (True|False, [list-of-errors])
        """
        infos = []
        if not isinstance(enmapBoxApp, EnMAPBoxApplication):
            infos.append('Not an EnMAPBoxApplication "{}"'.format(str(enmapBoxApp)))
        else:
            if not isinstance(enmapBoxApp.name, str) or len(enmapBoxApp.name.strip()) == 0:
                infos.append('Application name is undefined')
            if not isinstance(enmapBoxApp.version, str) or len(enmapBoxApp.version.strip()) == 0:
                infos.append('Application version is undefined')
            if not isinstance(enmapBoxApp.licence, str) or len(enmapBoxApp.licence.strip()) == 0:
                infos.append('Application licence is undefined')
        return len(infos) == 0, infos

    sigFileCreated = pyqtSignal(str)

    def __init__(
            self,
            enmapBox=Optional[EnMAPBox],  # make it optional to allow QGIS stand-alone apps like GEE TSE
            parent=None
    ):
        super(EnMAPBoxApplication, self).__init__(parent)
        self.enmapbox = enmapBox

        if enmapBox is None:
            from qgis.utils import iface
            self.qgis: QgisInterface = iface
        else:
            self.qgis: QgisInterface = enmapBox.iface

        # required attributes. Must be different to None
        self.name: str = None
        self.version: str = None
        self.licence: str = 'GNU GPL-3'

        # optional attributes, can be None
        self.projectWebsite: str = None
        self.description: str = None

    def removeApplication(self):
        """
        Overwrite to remove components of your application when this app is disabled.
        """
        return None

    def icon(self) -> QIcon:
        """
        Overwrite to return a QIcon
        http://doc.qt.io/qt-5/qicon.html
        :return:
        """
        return None

    def menu(self, appMenu):
        """
        :param appMenu: the EnMAP-Box' Application QMenu
        :return: None (default), the QMenu or QAction that is to be added to the QMenu "appMenu".
        """
        return None

    def geoAlgorithms(self) -> list:
        """
        Deprecated. Use processingAlgorithms() to return a list of QgsProcessingAlgorithms
        """
        raise Exception('Use "processingAlgorithms" instead.')

    def processingAlgorithms(self) -> list:

        return []

    @staticmethod
    def utilsAddActionInAlphanumericOrder(menu: QMenu, text: str) -> QAction:
        action = QAction(text, menu)
        actions = menu.actions()
        if len(actions) == 0:
            menu.addAction(action)
        elif action.text().lower() > actions[-1].text().lower():
            menu.addAction(action)
        else:
            before = actions[0]
            for a in actions[1:]:
                if action.text().lower() > before.text().lower():
                    before = a
                else:
                    break
            menu.insertAction(before, action)
        return action

    @staticmethod
    def utilsAddMenuInAlphanumericOrder(menu: QMenu, title: str) -> QMenu:
        submenu = QMenu(title, menu)
        actions = menu.actions()
        if len(actions) == 0:
            menu.addMenu(submenu)
        elif submenu.title().lower() > actions[-1].text().lower():
            menu.addMenu(submenu)
        else:
            before = actions[0]
            for a in actions[1:]:
                if submenu.title().lower() > before.text().lower():
                    before = a
                else:
                    break
            menu.insertMenu(before, submenu)
        return submenu


class ApplicationWrapper(QObject):
    """
    Stores information about an initialized EnMAPBoxApplication
    """

    def __init__(self, app: EnMAPBoxApplication, parent=None):
        super(ApplicationWrapper, self).__init__(parent)
        assert isinstance(app, EnMAPBoxApplication)
        self.app = app
        self.appId = '{}.{}'.format(app.__class__, app.name)
        self.menuItems = []
        self.processingAlgorithms = []


class ApplicationRegistry(QObject):
    """
    Registry to load and remove EnMAPBox Applications
    """

    sigLoadingInfo = pyqtSignal(str)
    sigLoadingFinished = pyqtSignal(bool, str)

    def __init__(self, enmapBox, parent=None):
        super(ApplicationRegistry, self).__init__(parent)
        self.appPackageRootFolders = []
        assert isinstance(enmapBox, EnMAPBox)

        self.mEnMAPBox = enmapBox
        self.mAppWrapper = collections.OrderedDict()

        self.mAppInitializationMessages = collections.OrderedDict()

    def __len__(self):
        return len(self.mAppWrapper)

    def __iter__(self):
        return iter(self.mAppWrapper.values())

    def applications(self) -> list:
        """
        Returns the EnMAPBoxApplications
        :return: [list-of-EnMAPBoxApplications]
        """
        return [w.app for w in self.applicationWrapper()]

    def applicationWrapper(self, nameOrApp=None) -> list:
        """
        Returns the EnMAPBoxApplicationWrappers.
        :param nameOrApp: str | EnMAPBoxApplication to return the ApplicationWrapper for
        :return: [list-of-EnMAPBoxApplicationWrappers]
        """
        wrappers = [w for w in self.mAppWrapper.values()]
        if nameOrApp is not None:
            wrappers = [w for w in wrappers if
                        isinstance(w, ApplicationWrapper) and nameOrApp in [w.appId, w.app.name, w.app]]
        return wrappers

    def addApplicationListing(self, path: str):
        """
        Loads EnMAPBoxApplications from locations defined in a text file
        :param path: str, filepath to file with locations of EnMAPBoxApplications
        """
        path = pathlib.Path(path)
        assert os.path.isfile(path)

        with open(path, 'r', encoding='utf-8') as file:
            app_locations = file.readlines()
            app_locations = [line.strip() for line in app_locations]
            app_locations = [pathlib.Path(line) for line in app_locations if len(line) > 0 and not line.startswith('#')]

        app_folders = []
        for app_path in app_locations:
            assert isinstance(app_path, pathlib.Path)
            if not app_path.is_absolute():
                app_path = path.parent / app_path
            if app_path.is_dir():
                app_folders.append(app_path)

        for app_folder in app_folders:
            self.addApplicationFolder(app_folder)

    def isApplicationFolder(self, path: pathlib.Path) -> bool:
        """
        Checks if the directory "appPackage" contains an '__init__.py' with an enmapboxApplicationFactory
        :param appPackage: path to directory
        :return: True | False
        """
        path = pathlib.Path(path)
        if not path.is_dir():
            return False

        pkgFile = path / '__init__.py'
        if not pkgFile.is_file():
            return False

        fileStats = os.stat(pkgFile)
        if fileStats.st_size > 1 * 1024 ** 2:  # assumes that files larger 1 MByte are not source code any more
            return False

        with open(pkgFile, encoding='utf-8') as file:
            lines = file.read()

        return re.search(r'def\s+enmapboxApplicationFactory\(.+\)\s*(->[^:]+)?:', lines) is not None

    def findApplicationFolders(self,
                               rootDir: pathlib.Path,
                               max_deep: int = 2) -> typing.List[pathlib.Path]:
        """
        Searches for folders that contain an EnMAPBoxApplication
        :param rootDir: str, root path directory
        :return: [list-of-str]
        """
        rootDir = pathlib.Path(rootDir)
        if max_deep < 0 or not rootDir.is_dir():
            return []

        if self.isApplicationFolder(rootDir):
            return [rootDir]
        else:
            # traverse subdirectories
            results = []
            for entry in os.scandir(rootDir):
                if entry.is_dir():
                    results.extend(
                        self.findApplicationFolders(entry.path, max_deep=max_deep - 1)
                    )
            return results

    def addApplicationFolder(self, app_folder: pathlib.Path) -> bool:
        """
        Loads EnMAP-Box application from ann application folder.
        Searches in folder and each sub-folder for EnMAP-Box Applications
        :param app_folder: directory with an __init__.py which defines a .enmapboxApplicationFactory() or
                               directory without any __init__.py which contains EnMAPBoxApplication folders
        :return: bool, True if any EnMAPBoxApplication was added
        """
        app_folder = pathlib.Path(app_folder)

        self.sigLoadingInfo.emit(f'Load Applications from {app_folder}')

        app_folders = self.findApplicationFolders(app_folder)
        if len(app_folders) == 0:
            return False
        elif len(app_folders) > 1:
            return any([self.addApplicationFolder(f) for f in app_folders])
        else:
            app_folder = app_folders[0]
            basename = os.path.basename(app_folder)
            try:

                appPkgName = app_folder.name
                appPkgRoot = app_folder.parent
                pkgFile = os.path.join(app_folder, '__init__.py')

                blacklist = os.environ.get('EMB_APP_BLACKLIST', '').split(',')
                if appPkgName in blacklist:
                    raise Exception('Skipped loading EnMAPBoxApplication "{}"'.format(appPkgName))

                print('Load EnMAPBoxApplication(s) from "{}"'.format(appPkgName))

                if not os.path.isfile(pkgFile):
                    raise Exception('File does not exist: "{}"'.format(pkgFile))

                site.addsitedir(appPkgRoot)

                # do not use __import__
                # appModule = __import__(appPkgName)

                appModule = importlib.import_module(appPkgName)

                factory = [o[1] for o in
                           inspect.getmembers(appModule, inspect.isfunction)
                           if o[0] == 'enmapboxApplicationFactory']

                if len(factory) == 0:
                    raise Exception('Missing definition of enmapboxApplicationFactory() in {}'.format(pkgFile))

                factory = factory[0]

                # create the app
                apps = factory(self.mEnMAPBox)
                if not isinstance(apps, list):
                    apps = [apps]

                if len(apps) == 0:
                    self.mAppInitializationMessages[basename] = None
                    return False

                foundValidApps = False

                for app in apps:
                    if not isinstance(app, EnMAPBoxApplication):
                        raise Exception('Not an EnMAPBoxApplication instance: {}'.format(app.__module__))
                    else:
                        result = self.addApplication(app)
                        foundValidApps = True

                if foundValidApps:
                    # return True if app  factory returned a valid EnMAPBoxApplication
                    self.mAppInitializationMessages[basename] = True
                else:
                    # return False if app factory did not return any EnMAPBoxApplication
                    self.mAppInitializationMessages[basename] = False
                return foundValidApps

            except Exception as ex:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tbLines = traceback.format_tb(exc_traceback)
                traceback.print_exc()  # AR: also print the traceback to the console for better PyCharm debugging
                tbLines = ''.join(tbLines)
                info = '{}:{}\nTraceback:\n{}'.format(ex.__class__.__name__, ex, tbLines)
                # return Error with Traceback
                self.mAppInitializationMessages[basename] = info
                print(info, file=sys.stderr)
                return False

    def addApplications(self, apps) -> list:
        """
        Adds a list of EnMAP-Box applications with addApplication
        :param apps: [list-of-EnMAPBoxApplications]
        :return:
        """
        return [self.addApplication(app) for app in apps]

    def addApplication(self, app: EnMAPBoxApplication) -> bool:
        """
        Adds a single EnMAP-Box application, i.a. a class that implemented the EnMAPBoxApplication Interface
        :param app: EnMAPBoxApplication
        """
        if DEBUG:
            print('addApplication({})'.format(str(app)))
        assert isinstance(app, EnMAPBoxApplication)

        appWrapper = ApplicationWrapper(app)
        self.sigLoadingInfo.emit(f'Load {appWrapper.app.name} ...')
        if DEBUG:
            print('Check requirements...')
        isOk, errorMessages = EnMAPBoxApplication.checkRequirements(app)
        if not isOk:
            self.sigLoadingInfo.emit(f'Unable to load {appWrapper.appId}', False)
            raise Exception(
                'Unable to load EnMAPBoxApplication "{}"\n{}.'.format(appWrapper.appId, '\n\t'.join(errorMessages)))
        if appWrapper.appId in self.mAppWrapper.keys():
            messageLog('EnMAPBoxApplication {} already loaded. Reload'.format(appWrapper.appId))
            self.removeApplication(appWrapper.appId)

        self.mAppWrapper[appWrapper.appId] = appWrapper

        # load GUI integration
        if DEBUG:
            print('Load menu items...')

        self.loadMenuItems(appWrapper)

        # load QGIS Processing Framework Integration
        import enmapbox.algorithmprovider
        if isinstance(enmapbox.algorithmprovider.instance(), enmapbox.algorithmprovider.EnMAPBoxProcessingProvider):
            self.loadProcessingAlgorithms(appWrapper)

        if DEBUG:
            print('Loading done.')
        self.sigLoadingFinished.emit(True, f'{app} loaded')
        return True

    def loadProcessingAlgorithms(self, appWrapper: ApplicationWrapper):
        self.sigLoadingInfo.emit(f'Load QgsProcessingAlgorithms of {appWrapper.app.name}')
        assert isinstance(appWrapper, ApplicationWrapper)
        processingAlgorithms = appWrapper.app.processingAlgorithms()
        if DEBUG:
            print('appWrapper.app.geoAlgorithms() returned: {}'.format(processingAlgorithms))

        if not isinstance(processingAlgorithms, list):
            processingAlgorithms = [processingAlgorithms]

        processingAlgorithms = [g for g in processingAlgorithms if isinstance(g, QgsProcessingAlgorithm)]

        if len(processingAlgorithms) > 0:
            processingAlgorithms = [alg.createInstance() for alg in processingAlgorithms]
            if DEBUG:
                print('QgsProcessingAlgorithms found: {}'.format(processingAlgorithms))
            appWrapper.processingAlgorithms.extend(processingAlgorithms)
            import enmapbox.algorithmprovider
            provider = enmapbox.algorithmprovider.instance()

            if isinstance(provider, EnMAPBoxProcessingProvider):
                provider.addAlgorithms(processingAlgorithms)
            else:
                print('Can not find EnMAPBoxAlgorithmProvider')

    def loadMenuItems(self, appWrapper: ApplicationWrapper, parentMenuName='Applications'):
        """
        Adds an EnMAPBoxApplication QMenu to its parent QMenu
        :param appWrapper:
        :param parentMenuName:
        :return:
        """
        assert isinstance(appWrapper, ApplicationWrapper)
        app = appWrapper.app
        assert isinstance(app, EnMAPBoxApplication)
        parentMenu = self.mEnMAPBox.menu(parentMenuName)
        items = app.menu(parentMenu)

        if items is not None:
            if not isinstance(items, list):
                items = [items]
            appWrapper.menuItems.extend(items)

    def reloadApplication(self, appId: str):
        """
        Reloads an EnMAP-Box Application
        :param appId: str
        """
        assert appId in self.mAppWrapper.keys()
        self.removeApplication(appId)
        self.addApplication(appId)

    def removeApplication(self, appId):
        """
        Removes the EnMAPBoxApplication
        :param appId: str
        """
        if isinstance(appId, EnMAPBoxApplication):
            appId = ApplicationWrapper(appId).appId

        appWrapper = self.mAppWrapper.pop(appId)
        assert isinstance(appWrapper, ApplicationWrapper)

        # remove menu item
        for item in appWrapper.menuItems:

            parent = item.parent()
            if isinstance(parent, QMenu):
                if isinstance(item, QMenu):
                    parent.removeAction(item.menuAction())
                else:
                    s = ""

        import enmapbox.algorithmprovider
        provider = enmapbox.algorithmprovider.instance()
        assert isinstance(provider, EnMAPBoxProcessingProvider)
        provider.removeAlgorithms(appWrapper.processingAlgorithms)
