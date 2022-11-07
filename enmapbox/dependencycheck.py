# -*- coding: utf-8 -*-
"""
***************************************************************************
    dependencychecker

    This module contains functionality to check the calling python environment for required packages and return
    user-friendly warning in case of missing dependencies.

    ---------------------
    Date                 : Januar 2018
    Copyright            : (C) 2018 by Benjamin Jakimow
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
import enum
import importlib
import os
import pathlib
import re
import shutil
import subprocess
# noinspection PyPep8Naming
import sys
import time
import typing
from difflib import SequenceMatcher
from typing import List

import requests

from enmapbox import debugLog
from enmapbox.qgispluginsupport.qps.utils import qgisAppQgisInterface
from enmapbox.settings import EnMAPBoxSettings
from qgis.PyQt import sip
from qgis.PyQt.QtCore import \
    pyqtSignal, pyqtSlot, Qt, \
    QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QRegExp, QUrl
from qgis.PyQt.QtGui import QContextMenuEvent, QColor, QIcon
from qgis.PyQt.QtWidgets import \
    QMessageBox, QStyledItemDelegate, QApplication, QTableView, QMenu, \
    QDialogButtonBox, QWidget
from qgis.core import QgsTask, QgsApplication, QgsTaskManager, QgsAnimatedIcon
from qgis.gui import QgsFileDownloaderDialog

URL_PACKAGE_HELP = r"https://enmap-box.readthedocs.io/en/latest/usr_section/usr_installation.html#install-required-python-packages"

INFO_MESSAGE_BEFORE_PACKAGE_INSTALLATION = f"""
<b>It might be necessary to install missing package(s) with your local package manager!</b>
  <p>You can find more information on how to install them <a href="{URL_PACKAGE_HELP}">here</a>
  <p>You may Ignore and install missing packages anyway or Abort the installation.</p>
"""

# look-up for pip package name and how it gets imported in python
# e.g. 'pip install scikit-learn' installs a package that is imported via 'import sklearn'
# Keys need to be lowercase, as accepted by PIP
PACKAGE_LOOKUP = {'scikit-learn': 'sklearn',
                  'PyOpenGL': 'OpenGL',
                  'enpt-enmapboxapp': 'enpt_enmapboxapp',
                  'GDAL': 'osgeo.gdal'
                  }

# just in case a package cannot /should not simply get installed
# calling pip install --user <pip package name>
INSTALLATION_HINT = {
    # 'enpt_enmapboxapp' : 'git+https://gitext.gfz-potsdam.de/EnMAP/GFZ_Tools_EnMAP_BOX/enpt_enmapboxapp.git'
}

INSTALLATION_BLOCK = {  # 'numba': 'should to be installed manually using the local package manager.\n' +
    #         'please read <a href="https://numba.pydata.org/numba-doc/dev/user/installing.html">' +
    #         'https://numba.pydata.org/numba-doc/dev/user/installing.html</a> for details',
    'numpy': 'needs to be installed/updated manually with local package manager (e.g. OSGeo4W Setup under Windows)',
    'GDAL': 'needs to be installed/updated manually with local package manager (e.g. OSGeo4W Setup under Windows)',
    'h5py': 'needs to be installed/updated manually with local package manager (e.g. OSGeo4W Setup under Windows); also see issue #868'
}

# https://packaging.python.org/tutorials/packaging-projects/#uploading-your-project-to-pypi
# pip package names: "name is the distribution name of your package.
# This can be any name as long as only contains letters, numbers, _ , and -."
rxPipPackageName = re.compile(r'^[a-zA-Z]+[a-zA-Z0-9-_]*')
rxPipVersion = re.compile(r'([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?'
                          + r'(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?')

for k in PACKAGE_LOOKUP.keys():
    assert rxPipPackageName.search(k)


class PIPPackage(object):

    def __init__(self, pyPkg: str, pipCmd: str = None):

        assert isinstance(pyPkg, str)
        assert len(pyPkg) > 0

        if pipCmd is None:
            pipCmd = PACKAGE_LOOKUP.get(pyPkg, pyPkg)
        pipCmd = pipCmd.strip()
        pipName = re.search(r'^[^<>=| ]+', pipCmd).group()
        self.pyPkgName: str = pyPkg
        self.pipCmd: str = pipCmd
        self.pipPkgName = pipName
        self.localLocation: str = ''
        self.stderrMsg: str = ''
        self.stdoutMsg: str = ''

        self.mLatestVersion = '<unknown>'
        self.mInstalledVersion = ''
        self.mImportError = ''

        try:
            __import__(self.pyPkgName)
            self.mInstalledVersion = '<installed>'
        except ModuleNotFoundError as ex1:
            self.mInstalledVersion = '<not installed>'
            self.mImportError = f'{ex1}'
            print(f'Unable to import {self.pyPkgName}:\n {ex1}', file=sys.stderr)
        except Exception as ex:
            self.mInstalledVersion = '<installed>'
            self.mImportError = f'{ex}'
            print(f'Unable to import {self.pyPkgName}:\n {ex}', file=sys.stderr)

    def updateAvailable(self) -> bool:
        return self.mInstalledVersion < self.mLatestVersion

    KEY_SKIP_WARNINGS = 'PIPInstaller/SkipWarnings'

    def packagesWithoutWarning(self) -> List[str]:
        return EnMAPBoxSettings().value(self.KEY_SKIP_WARNINGS, defaultValue='', type=str).split(',')

    def warnIfNotInstalled(self) -> bool:
        return self.pyPkgName not in self.packagesWithoutWarning()

    def setWarnIfNotInstalled(self, b: bool = True):
        noWarning = self.packagesWithoutWarning()
        if b and self.pyPkgName in noWarning:
            noWarning.remove(self.pyPkgName)
        elif not b and self.pyPkgName not in noWarning:
            noWarning.append(self.pyPkgName)
        EnMAPBoxSettings().setValue(self.KEY_SKIP_WARNINGS, ','.join(noWarning))

    def __str__(self):
        return '{}'.format(self.pyPkgName)

    def __eq__(self, other):
        if not isinstance(other, PIPPackage):
            return False
        return self.pyPkgName == other.pyPkgName

    def installPackage(self, *args, **kwds):

        self.stderrMsg = ''
        self.stdoutMsg = ''

        if self.pipPkgName in INSTALLATION_BLOCK.keys():
            self.stdoutMsg = ''
            self.stderrMsg = 'Blocked pip install {}'.format(self.pipPkgName) + \
                             '\nReason: {}'.format(INSTALLATION_BLOCK[self.pipPkgName]) + \
                             '\nPlease install manually with your local package manager'
        else:
            args = self.installArgs(*args, **kwds)
            cmd = ' '.join(args)
            try:
                process = subprocess.run(cmd,
                                         check=True,
                                         shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         universal_newlines=True)
                self.stdoutMsg = str(process.stdout)
            except subprocess.CalledProcessError as ex:
                self.stderrMsg = ex.stderr
            except Exception as ex2:
                self.stderrMsg = str(ex2)

    def installArgs(self, user: bool = True, upgrade: bool = False) -> typing.List[str]:

        # find path of local pip executable
        args = []
        if False:
            if shutil.which('pip3'):
                args.append('pip3')
            elif shutil.which('python3'):
                args.append('python3 -m pip')
            elif shutil.which('pip'):
                args.append('pip')
            elif shutil.which('python'):
                args.append('python -m pip')
            else:
                args.append('pip')
        else:
            args.append(str(localPythonExecutable()) + ' -m pip')

        args.append('install')
        if user:
            args.append('--user')

        if upgrade:
            args.append('--upgrade')
        args.append(self.pipCmd)
        return args

    def installCommand(self, *args, **kwds) -> str:
        """
        Returns the installation command as string
        :param args:
        :param kwds:
        :return: str
        """
        return ' '.join(self.installArgs(*args, **kwds))

    def updateCommand(self) -> str:
        """
        Returns the update command as string
        :return: str
        """
        return self.installCommand(upgrade=True)

    def isInstalled(self) -> bool:
        """
        Returns True if the package is installed and can be imported in python
        :return:
        :rtype:
        """
        try:
            spam_spec = importlib.util.find_spec(self.pyPkgName)
            return spam_spec is not None
        except KeyError:
            # https://github.com/EnMAP-Box/enmap-box/issues/215
            try:
                __import__(self.pyPkgName)
                return True
            except ModuleNotFoundError:
                return False
        return False



def localPythonExecutable() -> pathlib.Path:
    """
    Searches for the local python executable
    :return:
    """

    candidates = [shutil.which('python3'),
                  shutil.which('python')]

    candidates = [c for c in candidates if isinstance(c, str) and os.path.isfile(c)]

    r = os.path.dirname(os.__file__)
    similarity = [SequenceMatcher(None, r, c).ratio() for c in candidates]

    pyexe = candidates[similarity.index(max(similarity))]
    return pathlib.Path(pyexe)


class PIPPackageInfoTask(QgsTask):
    sigMessage = pyqtSignal(str, bool)
    sigInstalledVersion = pyqtSignal(str, str)
    sigAvailableVersion = pyqtSignal(str, str)
    sigAvailableVersionJson = pyqtSignal(str, dict)

    def __init__(self, description: str,
                 pipPackages: typing.List[str],
                 load_latest_versions: bool = True,
                 callback=None):
        super().__init__(description, QgsTask.CanCancel)
        self.packages: typing.List[str] = pipPackages
        self.callback = callback
        self.INSTALLED_VERSIONS = dict()
        self.LATEST_VERSIONS = dict()
        self.LATEST_VERSION_JSON = dict()
        self.load_latest_versions: bool = load_latest_versions

    def run(self):
        # pip version identifier
        # see https://www.python.org/dev/peps/pep-0440/#appendix-b-parsing-version-strings-with-regular-expressions
        nTotal = len(self.packages) + 1
        # get info on installed packages
        cmdList = str(localPythonExecutable()) + ' -m pip list'
        self.sigMessage.emit('Search for installed versions...', False)
        process = subprocess.run(cmdList,
                                 check=True, shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)

        rxInstalled = re.compile(r'({})\s+({})'.format(rxPipPackageName.pattern, rxPipVersion.pattern))
        stdout = process.stdout
        for line in process.stdout.splitlines():
            match = rxInstalled.search(line)
            if match:
                pipPkg = match.group(1)
                version = match.group(2)
                if pipPkg in self.packages:
                    self.sigInstalledVersion.emit(pipPkg, version)
                    self.INSTALLED_VERSIONS[pipPkg] = version
                else:
                    s = ""
                    # print('no requested: {}'.format(pipPkg))

        if not self.load_latest_versions:
            return True

        self.setProgress(1)

        # get info about remote package versions
        self.sigMessage.emit('Search for latest versions...', False)

        import warnings
        warnings.simplefilter('ignore', ResourceWarning)

        session = requests.Session()
        for i, pipPkg in enumerate(self.packages):
            self.LATEST_VERSIONS[pipPkg] = ""

            url = "https://pypi.python.org/pypi/{}/json".format(pipPkg)
            jsonDict = dict()
            version = ''
            with session.get(url) as response:
                if response.status_code == 200:
                    jsonDict = response.json()
                else:
                    info = 'request: "{}"\nreturned: {}\nstatus code: {}'.format(response.request.url,
                                                                                 response.reason,
                                                                                 response.status_code)
                    self.sigMessage.emit(info, True)

            if isinstance(jsonDict, dict) and len(jsonDict) > 0:
                version = jsonDict['info']['version']
                pipName = jsonDict['info']['name']
                if pipName != pipPkg:
                    self.sigMessage.emit('PIP Package "{}" is correctly written "{}"'.format(pipPkg, pipName), True)
                self.sigMessage.emit('Latest version "{}" = {}'.format(pipName, version), False)
            self.sigAvailableVersionJson.emit(pipPkg, jsonDict)
            self.sigAvailableVersion.emit(pipPkg, version)

            if self.isCanceled():
                session.close()
                self.sigMessage.emit('version retrieval canceled', False)
                return False
            self.setProgress(i + 2)
        session.close()
        return True

    def finished(self, result):
        if self.callback is not None:
            self.callback(result, self)


class InstallationState(enum.Enum):
    Unknown = 'unknown'
    NotInstalled = '<not installed>'
    Installed = '<installed>'
    LoadingError = '<loading error>'


class PIPInstallCommandTask(QgsTask):
    sigMessage = pyqtSignal(str, bool)

    def __init__(self, description: str, packages: typing.List[PIPPackage], upgrade=True, user=True, callback=None):
        super().__init__(description, QgsTask.CanCancel)
        self.packages: typing.List[PIPPackage] = packages
        self.callback = callback
        self.mUpgrade: bool = upgrade
        self.mUser: bool = user

    def run(self):
        n = len(self.packages)
        for i, pkg in enumerate(self.packages):
            assert isinstance(pkg, PIPPackage)
            self.sigMessage.emit(pkg.installCommand(user=self.mUser, upgrade=self.mUpgrade), False)
            pkg.installPackage(user=self.mUser, upgrade=self.mUpgrade)
            if len(pkg.stdoutMsg) > 0:
                self.sigMessage.emit(pkg.stdoutMsg, False)
            if len(pkg.stderrMsg) > 0:
                self.sigMessage.emit(pkg.stderrMsg, True)

            if self.isCanceled():
                return False
            self.setProgress(i + 1)
        return True

    def finished(self, result):

        if self.callback is not None:
            self.callback(result, self)


def checkGDALIssues() -> typing.List[str]:
    """
    Tests for known GDAL issues
    :return: list of errors / known problems
    """
    from osgeo import ogr
    issues = []
    drv = ogr.GetDriverByName('GPKG')

    if not isinstance(drv, ogr.Driver):
        info = 'GDAL/OGR installation does not support the GeoPackage (GPKG) vector driver'
        info += '(https://gdal.org/drivers/vector/gpkg.html).\n'
        issues.append(info)
    return issues


def requiredPackages(return_tuples: bool = False) -> typing.List[PIPPackage]:
    """
    Returns a list of pip packages that should be installable according to the `requirements.txt` file
    :return: [list of strings]
    :rtype: list
    """

    # see https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
    # for details of requirements format

    file = pathlib.Path(__file__).resolve().parents[1] / 'requirements.txt'
    assert file.is_file(), '{} does not exist'.format(file)
    packages = []
    rxPipPkg = re.compile(r'^[a-zA-Z_-][a-zA-Z0-9_-]*')

    with open(file, 'r') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]

        # A line that begins with # is treated as a comment and ignored.
        lines = [line for line in lines if not line.startswith('#') and len(line) > 0]

        # Whitespace followed by a # causes the # and the remainder of the line to be treated as a comment.
        lines = [line.split(' #')[0] for line in lines]
        for line in lines:
            match = rxPipPkg.search(line)
            if match:
                pipPkg = match.group()
                pyPkg = PACKAGE_LOOKUP.get(pipPkg, pipPkg)
                cmd = INSTALLATION_HINT.get(pipPkg, line)
                debugLog('dependencycheck required package {}:{}:{}'.format(pyPkg, pipPkg, cmd))
                if return_tuples:
                    pkg = (pyPkg, pipPkg, cmd)
                else:
                    pkg = PIPPackage(pyPkg, cmd)
                packages.append(pkg)
    return packages


def missingPackages() -> typing.List[PIPPackage]:
    """
    Returns missing packages
    :return: [PIPPackage]
    :rtype:
    """
    return [p for p in requiredPackages() if not p.isInstalled() and p.warnIfNotInstalled()]


def missingPackageInfo(missing_packages: typing.List[PIPPackage], html=True) -> str:
    """
    Converts a list of missing packages into better readable output.
    :param missing_packages: list of uninstalled packages
    :param html: bool, set True (default) to return HTML output string
    :return: str
    """
    assert isinstance(missing_packages, list)
    for p in missing_packages:
        assert isinstance(p, PIPPackage)
    missing_packages = [p for p in missing_packages if isinstance(p, PIPPackage) and not p.isInstalled()]
    n = len(missing_packages)
    if n == 0:
        return None

    from enmapbox import DIR_REPO, URL_INSTALLATION
    info = ['The following {} package(s) are not installed:'.format(n), '<ol>']
    for i, pkg in enumerate(missing_packages):
        assert isinstance(pkg, PIPPackage)
        info.append('\t<li>{} (install by "{}")</li>'.format(pkg.pyPkgName, pkg.installCommand()))

    pathRequirementsTxt = os.path.join(DIR_REPO, 'requirements.txt')

    info.append('</ol>')
    info.append('<p>Please follow the installation guide <a href="{0}">{0}</a><br/>'.format(URL_INSTALLATION))
    info.append('and install missing packages, e.g. with pip:<br/><br/>')
    info.append('\t<code>$ python3 -m pip install -r {}</code></p><hr>'.format(pathRequirementsTxt))

    info = '\n'.join(info)

    if not html:
        info = re.sub('<br/>', '\n', info)
        info = re.sub('<[^>]*>', '', info)
    return info


def missingTestData() -> bool:
    """
    Returns (True, message:str) if testdata can not be loaded,
     (False, None) else
    :return: (bool, str)
    """
    try:
        import enmapbox.exampledata
        assert os.path.isfile(enmapbox.exampledata.enmap)
        return False
    except Exception as ex:
        print(ex, file=sys.stderr)
        return True


def installTestData(overwrite_existing: bool = False, ask: bool = True):
    """
    Downloads and installs the EnMAP-Box Example Data
    """
    if not missingTestData() and not overwrite_existing:
        print('Testdata already installed and up to date.')
        return

    app = QgsApplication.instance()
    if app is None:
        from enmapbox.testing import start_app
        app = start_app()
    from enmapbox import URL_TESTDATA
    from enmapbox import DIR_EXAMPLEDATA
    if ask is True:
        btn = QMessageBox.question(None, 'Testdata is missing or outdated',
                                   'Download testdata from \n{}\n?'.format(URL_TESTDATA))
        if btn != QMessageBox.Yes:
            print('Canceled')
            return

    pathLocalZip = os.path.join(os.path.dirname(DIR_EXAMPLEDATA), 'enmapboxexampledata.zip')
    url = QUrl(URL_TESTDATA)
    dialog = QgsFileDownloaderDialog(url, pathLocalZip, 'Download enmapboxexampledata.zip')
    qgisMainApp = qgisAppQgisInterface()

    def onCanceled():
        print('Download canceled')
        return

    def onCompleted():
        print('Download completed')
        print('Unzip {}...'.format(pathLocalZip))

        targetDir = pathlib.Path(DIR_EXAMPLEDATA)
        examplePkgName = targetDir.name
        os.makedirs(targetDir, exist_ok=True)
        import zipfile
        zf = zipfile.ZipFile(pathLocalZip)

        names = zf.namelist()
        # [n for n in names if re.search(r'[^/]/exampledata/..*', n) and not n.endswith('/')]

        subPaths = []
        rx = re.compile(f'/?({examplePkgName}/.+)$')
        for n in names:
            if not n.endswith('/'):
                m = rx.match(n)
                if isinstance(m, typing.Match):
                    subPaths.append(pathlib.Path(m.group(1)))

        assert len(subPaths) > 0, \
            f'Downloaded zip file does not contain data with sub-paths {examplePkgName}/*:\n\t{pathLocalZip}'

        for pathRel in subPaths:
            pathDst = targetDir.parent / pathRel
            # create directory if it doesn't exist
            os.makedirs(pathDst.parent, exist_ok=True)

            with open(pathDst, 'wb') as outfile:
                outfile.write(zf.read(pathRel.as_posix()))
                outfile.flush()

        zf.close()
        del zf

        print('Testdata installed.')
        spec = importlib.util.spec_from_file_location(examplePkgName, os.path.join(targetDir, '__init__.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[examplePkgName] = module
        # backward compatibility
        sys.modules['enmapboxtestdata'] = module

    def onDownloadError(messages):
        raise Exception('\n'.join(messages))

    def deleteFileDownloadedFile():

        pass
        # dirty patch for Issue #167
        #
        # print('Remove {}...'.format(pathLocalZip))
        # os.remove(pathLocalZip)

    def onDownLoadExited():

        from qgis.PyQt.QtCore import QTimer
        QTimer.singleShot(5000, deleteFileDownloadedFile)

    def onDownloadProgress(received, total):
        if not qgisMainApp and total > 0:
            print('\r{:0.2f} %'.format(100. * received / total), end=' ', flush=True)
            time.sleep(0.1)

    dialog.downloadCanceled.connect(onCanceled)
    dialog.downloadCompleted.connect(onCompleted)
    dialog.downloadError.connect(onDownloadError)
    dialog.downloadExited.connect(onDownLoadExited)
    dialog.downloadProgress.connect(onDownloadProgress)

    dialog.open()
    dialog.exec_()


class PIPPackageInstallerTableModel(QAbstractTableModel):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.cnPkg = 'Package'
        self.cnInstalledVersion = 'Installed'
        self.cnLatestVersion = 'Latest'
        self.cnCommand = 'Installation Command'
        self.mColumnNames = [self.cnPkg,
                             self.cnInstalledVersion,
                             self.cnLatestVersion,
                             self.cnCommand]
        self.mColumnToolTips = ['Python package name. <br>'
                                'Uncheck packages to hide warnings if they are missed during EnMAP-Box startup',
                                'Installed version',
                                'Latest version',
                                'Command to install/update the package from your command line interface']
        self.mPackages: List[PIPPackage] = []
        self.mWarned = False
        self.mUser = True

        self.mAnimatedIcon = QgsAnimatedIcon(QgsApplication.iconPath("/mIconLoading.gif"), self)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        cn = self.mColumnNames[index.column()]
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if cn == self.cnPkg:
            flags = flags | Qt.ItemIsUserCheckable
        return flags

    @pyqtSlot()
    def onFrameChange(self):

        s = ""

    def setData(self, index: QModelIndex, value, role=None):
        if not index.isValid():
            return None

        pkg = self.mPackages[index.row()]

        assert isinstance(pkg, PIPPackage)
        cn = self.mColumnNames[index.column()]

        changed = False
        if role == Qt.CheckStateRole:
            if cn == self.cnPkg:
                pkg.setWarnIfNotInstalled(value == Qt.Checked)
                changed = True

        if changed:
            idx0 = self.index(index.row(), 0, index.parent())
            idx1 = self.index(index.row(), self.columnCount() - 1, index.parent())
            self.dataChanged.emit(idx0, idx1, [role, Qt.ForegroundRole])
        return changed

    def setUser(self, b: bool):
        self.mUser = b is True
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount() - 1, self.columnCount() - 1))

    def packageFromPIPName(self, pipName: str) -> PIPPackage:
        for pkg in self:
            if pkg.pipPkgName.lower() == pipName.lower():
                return pkg
        return None

    def updateInstalledVersion(self, pipName: str, installedVersion: str):
        pkg = self.packageFromPIPName(pipName)
        if isinstance(pkg, PIPPackage):
            pkg.mInstalledVersion = installedVersion
            self.updatePackage(pkg)

    def updateAvailableVersion(self, pipName: str, availableVersion: str):
        pkg = self.packageFromPIPName(pipName)
        if isinstance(pkg, PIPPackage):
            pkg.mLatestVersion = availableVersion
            self.updatePackage(pkg)

    def updatePackage(self, pkg: PIPPackage):
        assert isinstance(pkg, PIPPackage)
        idx = self.pkg2index(pkg)
        if idx.isValid():
            r = idx.row()
            self.dataChanged.emit(self.createIndex(r, 0),
                                  self.createIndex(r, self.columnCount() - 1))

    def __getitem__(self, slice):
        return self.mPackages[slice]

    def __contains__(self, item):
        return item in self.mPackages

    def __len__(self):
        return len(self.mPackages)

    def __iter__(self) -> typing.Iterator[PIPPackage]:
        return iter(self.mPackages)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.mPackages)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self.mColumnNames)

    def pkg2index(self, pkg: PIPPackage) -> QModelIndex:
        assert pkg in self.mPackages
        return self.index(self.mPackages.index(pkg), 0)

    def headerData(self, col, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.mColumnNames[col]
            if role == Qt.ToolTipRole:
                return self.mColumnToolTips[col]

        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return col
        return None

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        pkg = self.mPackages[row]
        return self.createIndex(row, column, pkg)

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:

        if not index.isValid():
            return None

        pkg = self.mPackages[index.row()]

        assert isinstance(pkg, PIPPackage)
        cn = self.mColumnNames[index.column()]

        if role == Qt.DisplayRole:
            if cn == self.cnPkg:
                return pkg.pyPkgName

            if cn == self.cnInstalledVersion:
                return pkg.mInstalledVersion

            if cn == self.cnLatestVersion:
                return pkg.mLatestVersion

            if cn == self.cnCommand:
                cmd = pkg.installCommand(user=self.mUser, upgrade=pkg.mInstalledVersion < pkg.mLatestVersion)
                match = re.search(r'python(\.exe)?.*$', cmd, re.I)
                if match:
                    return match.group()
                else:
                    return cmd

        if role == Qt.ForegroundRole:
            if cn == self.cnInstalledVersion:
                if pkg.warnIfNotInstalled():
                    if pkg.mInstalledVersion == '<not installed>':
                        return QColor('red')
                    else:
                        return QColor('green')
                elif pkg.mLatestVersion > pkg.mInstalledVersion:
                    return QColor('orange')

        if role == Qt.ToolTipRole:
            if cn == self.cnPkg:
                return self.mColumnNames[index.column()]

            if cn == self.cnCommand:
                info = 'Command to install/update {} from your CLI.'.format(pkg.pyPkgName)
                if 'git+' in pkg.installCommand():
                    info += '\nThis command requires having git (https://www.git-scm.com) installed!'
                return info

        if role == Qt.CheckStateRole:
            if cn == self.cnPkg:
                return Qt.Checked if pkg.warnIfNotInstalled() else Qt.Unchecked

        if role == Qt.DecorationRole and index.column() == 0:
            if pkg.mLatestVersion == '<unknown>':
                return QIcon(':/images/themes/default/mIconLoading.gif')

        if role == Qt.UserRole:
            return pkg

    def addPackages(self, packages: typing.List[PIPPackage]):

        if len(packages) > 0:
            for p in packages:
                assert isinstance(p, PIPPackage)
            n = self.rowCount()
            self.beginInsertRows(QModelIndex(), n, n + len(packages) - 1)
            self.mPackages.extend(packages)
            self.endInsertRows()

    def removePackages(self):
        pass


class TableViewDelegate(QStyledItemDelegate):

    def __init__(self, tableView: QTableView, parent=None):
        assert isinstance(tableView, QTableView)
        super().__init__(parent=parent)
        self.mTableView = tableView


class PIPPackageInstallerTableView(QTableView):
    sigInstallPackageRequest = pyqtSignal(list)
    sigPackageReloadRequest = pyqtSignal(list)

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """
        Opens the context menu
        """
        index = self.indexAt(event.pos())

        if not index.isValid():
            return

        pkg = index.data(Qt.UserRole)
        txt = index.data(Qt.DisplayRole)
        if not isinstance(pkg, PIPPackage):
            return
        pkgs = [idx.data(Qt.UserRole) for idx in self.selectionModel().selectedRows()]

        model = self.model().sourceModel()
        assert isinstance(model, PIPPackageInstallerTableModel)

        cmd = pkg.installCommand(user=model.mUser)
        m = QMenu()
        a = m.addAction('Copy')
        a.setToolTip('Copies the installation command')
        a.triggered.connect(lambda *args, v=txt: QApplication.clipboard().setText(v))

        a = m.addAction('Copy (executable)')
        a.setToolTip('Copies the installation command including path of python executable')
        a.triggered.connect(lambda *args, v=cmd: QApplication.clipboard().setText(v))

        isInstalled = pkg.isInstalled()
        isUpdatable = pkg.updateAvailable()

        a = m.addAction('Install/Update')
        a.setEnabled(not isInstalled or isUpdatable)
        a.triggered.connect(lambda *args, p=pkgs: self.sigInstallPackageRequest.emit(p))

        a = m.addAction('Reload')
        a.setToolTip('Reloads installed and available package versions')
        a.triggered.connect(lambda *args, p=pkgs: self.sigPackageReloadRequest.emit(pkgs))

        m.exec_(event.globalPos())


class PIPPackageInstaller(QWidget):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        from enmapbox.gui.utils import loadUi
        from enmapbox import DIR_UIFILES
        path = pathlib.Path(DIR_UIFILES) / 'pippackageinstaller.ui'
        loadUi(path, self)

        self.mWarned = False

        self.mTasks = dict()
        self.model = PIPPackageInstallerTableModel()
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.tableView.setModel(self.proxyModel)

        self.progressBar.setVisible(False)

        self.cbUser.toggled.connect(self.model.setUser)
        self.cbMissingOnly.toggled.connect(self.showMissingOnly)
        self.showMissingOnly(self.cbMissingOnly.isChecked())

        assert isinstance(self.tableView, PIPPackageInstallerTableView)
        self.tableView.setSortingEnabled(True)
        self.tableView.sigInstallPackageRequest.connect(self.installPackages)
        self.tableView.sigPackageReloadRequest.connect(self.reloadPythonPackages)
        self.tableView.sortByColumn(1, Qt.DescendingOrder)
        self.buttonBox.button(QDialogButtonBox.YesToAll).clicked.connect(self.installAll)
        self.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close)

        self.actionClearConsole.triggered.connect(self.textBrowser.clear)
        self.actionCopyConsole.triggered.connect(
            lambda: QgsApplication.instance().clipboard().setText(self.textBrowser.toPlainText()))
        self.btnClearConsole.setDefaultAction(self.actionClearConsole)
        self.btnCopyConsole.setDefaultAction(self.actionCopyConsole)

    def onProgressChanged(self, progress):
        self.progressBar.setValue(int(progress))

    def onCompleted(self, result: bool, task: PIPInstallCommandTask):
        if isinstance(task, PIPInstallCommandTask) and not sip.isdeleted(task):
            for pkg in task.packages:
                self.model.updatePackage(pkg)
            if result is False:
                self.progressBar.setValue(0)
            self.onRemoveTask(id(task))
            self.loadPIPVersionInfo(task.packages, load_latest_versions=False)
        elif isinstance(task, PIPPackageInfoTask) and not sip.isdeleted(task):
            s = ""
            self.onRemoveTask(id(task))

    def installAll(self):

        self.installPackages([p for p in self.model if not p.isInstalled()])

    def installPackages(self, packages: typing.List[PIPPackage]):

        if not self.showWarning():
            return
        for p in packages:
            assert isinstance(p, PIPPackage)
        pkgs = []
        for p in packages:
            if p not in pkgs:
                pkgs.append(p)
        # pkgs = [copy.deepcopy(p) for p in packages]
        pkgs = packages
        self.progressBar.setRange(0, len(pkgs))
        self.progressBar.setValue(-1)

        qgsTask = PIPInstallCommandTask('PIP installation', pkgs, callback=self.onCompleted)
        self.startTask(qgsTask)

    def reloadPythonPackages(self, pipPackages: typing.List[PIPPackage]):
        import importlib
        for pkg in pipPackages:
            try:
                module = __import__(pkg.pyPkgName)
                importlib.reload(module)
                info = '{} reloaded'.format(module)
                self.addText(info, True)
            except Exception as ex:
                self.addText(str(ex), True)

    def loadPIPVersionInfo(self, pipPackages: typing.List[PIPPackage], load_latest_versions: bool = True):
        if len(pipPackages) == 0:
            pipPackages = self.model[:]
        else:
            for p in pipPackages:
                assert isinstance(p, PIPPackage)
        # get names
        pipPackageNames = [p.pipPkgName for p in pipPackages]

        task = PIPPackageInfoTask('Get package information', pipPackageNames, load_latest_versions=load_latest_versions)
        task.sigInstalledVersion.connect(self.model.updateInstalledVersion)
        task.sigAvailableVersion.connect(self.model.updateAvailableVersion)
        self.startTask(task)

    def startTask(self, qgsTask: QgsTask):
        tid = id(qgsTask)

        qgsTask.progressChanged.connect(self.onProgressChanged)
        qgsTask.taskCompleted.connect(lambda *args, tid=tid: self.onRemoveTask(tid))
        qgsTask.taskTerminated.connect(lambda *args, tid=tid: self.onRemoveTask(tid))
        qgsTask.sigMessage.connect(self.onTaskMessage)
        self.mTasks[tid] = qgsTask
        tm = QgsApplication.taskManager()
        assert isinstance(tm, QgsTaskManager)
        tm.addTask(qgsTask)

    def onTaskMessage(self, msg: str, is_error: bool):
        if is_error:
            self.addText(msg, QColor('red'))
        else:
            self.addText(msg)

    def onRemoveTask(self, tid):
        if tid in self.mTasks.keys():
            del self.mTasks[tid]

    def showWarning(self) -> bool:
        """
        Opens the warning to
        :return:
        :rtype:
        """
        if not self.mWarned:

            box = QMessageBox(QMessageBox.Information,
                              'Package Installation',
                              INFO_MESSAGE_BEFORE_PACKAGE_INSTALLATION,
                              QMessageBox.Abort | QMessageBox.Ignore)
            box.setTextFormat(Qt.RichText)
            box.setDefaultButton(QMessageBox.Abort)
            result = box.exec_()

            if result == QMessageBox.Abort:
                return False
            else:
                self.mWarned = True
                return True
        else:
            return True

    def showMissingOnly(self, b: bool):
        if b:
            self.proxyModel.setFilterRegExp(QRegExp('Not installed', Qt.CaseInsensitive, QRegExp.Wildcard))
        else:
            self.proxyModel.setFilterRegExp(None)

        self.proxyModel.setFilterKeyColumn(1)

    def addText(self, text: str, color: QColor = None):

        c = self.textBrowser.textColor()
        if isinstance(color, QColor):
            self.textBrowser.setTextColor(color)
        self.textBrowser.append(text)
        self.textBrowser.setTextColor(c)

    def addPackages(self, packages: typing.List[PIPPackage]):
        self.model.addPackages(packages)
        self.loadPIPVersionInfo(packages)
