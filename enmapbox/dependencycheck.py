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
from pip._internal.utils.misc import get_prog

import csv
import datetime
import enum
import importlib
import platform
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import typing
import warnings
from contextlib import redirect_stdout, redirect_stderr
from importlib.machinery import ModuleSpec
from io import StringIO
from pathlib import Path
from typing import List, Match, Iterator, Any, Dict, Tuple

from qgis.PyQt.QtCore import QProcess
from pip._internal.cli.main_parser import parse_command
from pip._internal.commands import create_command
from qgis.PyQt import sip
from qgis.PyQt.QtCore import \
    pyqtSignal, Qt, \
    QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QUrl
from qgis.PyQt.QtGui import QContextMenuEvent, QColor
from qgis.PyQt.QtWidgets import \
    QMessageBox, QStyledItemDelegate, QApplication, QTableView, QMenu, \
    QDialogButtonBox, QWidget
from qgis.core import Qgis
from qgis.core import QgsTask, QgsApplication, QgsTaskManager, QgsAnimatedIcon
from qgis.gui import QgsFileDownloaderDialog

from enmapbox import REQUIREMENTS_CSV
from enmapbox.enmapboxsettings import EnMAPBoxSettings
from enmapbox.qgispluginsupport.qps.utils import qgisAppQgisInterface

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

    @staticmethod
    def fromDict(info) -> 'PIPPackage':
        """
        Create a PIPPackage from data stored in a dictionary.
        :param info: dict
        :return: PIPPackage
        """
        assert isinstance(info, dict)
        for n in ['Name', 'name']:
            if n in info:
                pip_name = info[n]
                pkg = PIPPackage(pip_name)
                pkg.updateFromDict(info)
                return pkg
        return None

    def __init__(self,
                 pip_name: str,
                 py_name: str = None,
                 min_version: str = None,
                 used_by: List[str] = None,
                 comment: str = None):

        assert isinstance(pip_name, str)
        assert len(pip_name) > 0
        pip_name = pip_name.strip()
        if py_name is None:
            py_name = PACKAGE_LOOKUP.get(pip_name, pip_name)

        self.pyPkgName: str = py_name
        self.pipPkgName = pip_name

        self.location: str = ''
        self.stderrMsg: str = ''
        self.stdoutMsg: str = ''

        self.version_latest: str = '<unknown>'
        self.version: str = ''

        self.summary: str = ''
        self.license: str = ''
        self.requirements: str = ''
        self.homepage: str = ''

        self.mError: str = ''

        if self.isInstalled():
            self.version = '<installed>'
        else:
            self.version = '<not installed>'

    def __repr__(self):
        return super().__repr__() + f'"{self.pipPkgName}"'

    def updateFromDict(self, info: dict):
        info = {k.lower(): v for k, v in info.items()}
        assert 'name' in info
        assert info['name'] == self.pipPkgName

        if 'version' in info:
            self.version = info['version']

        if 'summary' in info:
            self.summary = info['summary']

        if 'location' in info:
            self.location = info['location']

        if 'license' in info:
            self.license = info['license']

        if 'requires' in info:
            self.requirements = info['requires']

        if 'home-page' in info:
            self.homepage = info['home-page']

        if 'latest_version' in info:
            self.version_latest = info['latest_version']
        s = ""

    def updateAvailable(self) -> bool:
        return self.version < self.version_latest

    KEY_SKIP_WARNINGS = 'PIPInstaller/SkipWarnings'

    def packagesWithoutWarning(self) -> List[str]:
        return EnMAPBoxSettings().value(self.KEY_SKIP_WARNINGS, defaultValue='', type=str).split(',')

    def skipStartupWarning(self) -> bool:
        return self.pyPkgName in self.packagesWithoutWarning()

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
        warnings.warn(DeprecationWarning('installPackage was deactivated'))
        return

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

    def installArgs(self, user: bool = True, upgrade: bool = False) -> List[str]:

        # find path of local pip executable
        args = ['pip', 'install']

        if user:
            args.append('--user')

        if upgrade:
            args.append('--upgrade')
        args.append(self.pipPkgName)
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
            if isinstance(spam_spec, ModuleSpec) and spam_spec.has_location:
                self.location = os.path.dirname(spam_spec.origin)
            return spam_spec is not None
        except Exception as ex:
            # https://github.com/EnMAP-Box/enmap-box/issues/215
            self.mError = str(ex)
        return False


_LOCAL_PIPEXE: Path = None


def localPipExecutable() -> Path:
    global _LOCAL_PIPEXE
    if _LOCAL_PIPEXE is None:
        pipexe = Path(get_prog())
        if not pipexe.is_file():
            pipexe = None

            p = platform.uname().system
            sysexe = Path(sys.executable)

            if p == 'Darwin' and '.app/Contents/MacOS' in sysexe.as_posix():
                path = sysexe
                while path.name != 'MacOS':
                    path = path.parent
                path = path / 'bin/pip'
                if path.is_file():
                    pipexe = path
            else:

                if p == 'Windows':
                    candidates = ['where pip', 'where pip3']
                else:
                    candidates = ['which pip', 'which pip3']

                for c in candidates:
                    process = QProcess()
                    process.start(c)
                    process.waitForFinished()
                    msgOut = process.readAllStandardOutput().data().decode('utf-8')
                    msgErr = process.readAllStandardError().data().decode('utf-8')
                    success = process.exitCode() == 0
                    if success and len(msgOut) > 0:
                        lines = msgOut.splitlines()
                        path = Path(lines[0])
                        if path.is_file():
                            pipexe = path
                            break
            if isinstance(pipexe, Path) and pipexe.is_file():
                _LOCAL_PIPEXE = pipexe
    return _LOCAL_PIPEXE


def localPythonExecutable() -> pathlib.Path:
    """
    Searches for the local python executable
    :return:
    """
    candidates = [pathlib.Path(sys.executable)]
    pythonhome = os.environ.get('PYTHONHOME', None)
    if pythonhome:
        pythonhome = pathlib.Path(pythonhome)
        ext = ''
        if 'windows' in platform.uname().system.lower():
            ext = '.exe'
        for n in ['python3', 'python']:
            candidates.extend([
                pythonhome / f'{n}{ext}',
                pythonhome / 'bin' / f'{n}{ext}'
            ])

    for c in candidates:
        c = pathlib.Path(c.resolve())
        if c.is_file() and 'python' in c.name.lower():
            return c

    return None


def call_pip_command(pipArgs):
    assert isinstance(pipArgs, list)

    success = 0
    msgOut = msgErr = None

    if True:
        pipexe = localPipExecutable()
        process = QProcess()
        process.start(f'{pipexe} ' + ' '.join(pipArgs))
        process.waitForFinished()
        msgOut = process.readAllStandardOutput().data().decode('utf-8')
        msgErr = process.readAllStandardError().data().decode('utf-8')
        success = process.exitCode() == 0
        if success or msgErr != '':
            return success, msgOut, msgErr

    if False:
        with redirect_stdout(io.StringIO()) as f_out, redirect_stderr(io.StringIO) as f_err:
            try:
                cmd_name, cmd_args = parse_command(pipArgs)
                cmd = create_command(cmd_name, isolated=("--isolated" in cmd_args))
                result = cmd.main(cmd_args)
                msgOut = f_out.getvalue()
                msgErr = f_err.getvalue()
                success = result == 0
            except Exception as ex:
                success = False
                msgErr = str(ex)

        return success, msgOut, msgErr

    if True:
        _std_out = sys.stdout
        _std_err = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        msgOut = None
        msgErr = None
        success = False
        try:
            cmd_name, cmd_args = parse_command(pipArgs)
            cmd = create_command(cmd_name, isolated=("--isolated" in cmd_args))
            result = cmd.main(cmd_args)
            msgOut = sys.stdout.getvalue()
            msgErr = sys.stderr.getvalue()
            success = result == 0
        except Exception as ex:
            success = False
            msgErr = str(ex)
        finally:
            sys.stdout = _std_out
            sys.stderr = _std_err

        return success, msgOut, msgErr


class PIPPackageInfoTask(QgsTask):
    sigMessage = pyqtSignal(str, Qgis.MessageLevel)

    sigPackageList = pyqtSignal(list)
    sigPackageUpdates = pyqtSignal(list)
    sigPackageInfo = pyqtSignal(list)

    def __init__(self, description: str = 'Update PyPI Status',
                 packages_of_interest: List[str] = [],
                 batch_size: int = 20,
                 poi_only: bool = False,
                 search_updates: bool = True,
                 search_info: bool = True,
                 callback=None):
        super().__init__(description, QgsTask.CanCancel)
        for p in packages_of_interest:
            assert isinstance(p, str)
        self._pois: List[str] = packages_of_interest
        self._callback = callback
        self._messages: Dict[str, Tuple[bool, str, str]] = dict()
        self._batch_size = batch_size
        self._poi_only: bool = poi_only
        self._search_updates: bool = search_updates
        self._search_info: bool = search_info

    def run(self):

        self.sigMessage.emit('Search for installed packages...', Qgis.MessageLevel.Info)
        msg = err = ''
        try:
            success, msg, err = call_pip_command(['list', '--format', 'json'])
            if success:
                pkg_all = json.loads(msg)
                self.sigPackageList.emit(pkg_all)
            else:
                self.sigMessage.emit(err, Qgis.MessageLevel.Critical)
                return False
            self._messages['list'] = (success, msg, err)
        except Exception as ex:
            err = str(ex)
            self._messages['list_err'] = (False, msg, err)
            self.sigMessage.emit(str(ex), Qgis.MessageLevel.Critical)
            return False
        self.setProgress(10)

        msg = err = ''
        if isinstance(pkg_all, list) and self._search_updates:
            self.sigMessage.emit('Search for available updates...', Qgis.MessageLevel.Info)
            try:
                success, msg, err = call_pip_command(['list', '-o', '--format', 'json'])
                if success:
                    pkg_updates = json.loads(msg)
                    self.sigPackageUpdates.emit(pkg_updates)
                else:
                    self.sigMessage.emit(err, Qgis.MessageLevel.Critical)
                    return False

                self._messages['updates'] = (success, msg, err)
            except Exception as ex:
                err = str(ex)
                self._messages['updates'] = (False, msg, err)
                self.sigMessage.emit(str(ex), Qgis.MessageLevel.Critical)
                return False

        self.setProgress(20)

        if isinstance(pkg_all, list) and self._search_info:
            self.sigMessage.emit('Fetch package details...', Qgis.MessageLevel.Info)

            if self._poi_only:
                pkg_all = [p for p in pkg_all if p['name'] in self._pois]
            else:
                if len(self._pois) > 0:
                    # search for packages of interest first, i.e. packages required to run the EnMAP-Box
                    pkg_all = sorted(pkg_all, key=lambda p: p['name'] not in self._pois)

            try:
                n = len(pkg_all)
                messages = []
                # for batch in itertools.batched(pkg_all, 10):
                batch_size = self._batch_size
                rxBlock = re.compile('\n---\n')  # this splits the numpy output into different packages
                rxLines = re.compile('\n(?=[^: ]+: )', re.M)  # this splits the package output into line blocks
                rxKeyValue = re.compile(r'^(?P<key>[^: ]+): (?P<value>.*)', re.DOTALL)

                for i in range(0, n, batch_size):
                    j = min(n, i + batch_size)
                    batch = pkg_all[i:j]
                    success, msg, err = call_pip_command(['show'] + [p['name'] for p in batch])
                    if success:
                        infoLinesAll = rxBlock.split(msg)
                        infoBatch = []
                        for infoLines in infoLinesAll:
                            packageInfos = dict()
                            lines = [line.strip() for line in rxLines.split(infoLines)]
                            lines = [line for line in lines if len(line) > 0]

                            for line in lines:
                                match = rxKeyValue.match(line)
                                if isinstance(match, typing.Match):
                                    packageInfos[match.group('key')] = match.group('value').strip()

                            if 'Name' in packageInfos:
                                messages.append(packageInfos['Name'])
                                infoBatch.append(packageInfos)
                        if len(infoBatch) > 0:
                            self.sigPackageInfo.emit(infoBatch)
                            progress = int(j / n * 80) + 20
                            self.setProgress(progress)
            except Exception as ex:

                self.sigMessage.emit(str(ex), Qgis.MessageLevel.Critical)
                self._messages['major_exception'] = str(ex)
                return False

        self.setProgress(100)
        return True

    def finished(self, result):
        if self._callback is not None:
            self._callback(result, self)


class InstallationState(enum.Enum):
    Unknown = 'unknown'
    NotInstalled = '<not installed>'
    Installed = '<installed>'
    LoadingError = '<loading error>'


class PIPInstallCommandTask(QgsTask):
    sigMessage = pyqtSignal(str, bool)

    def __init__(self, description: str, packages: List[PIPPackage], upgrade=True, user=True, callback=None):
        super().__init__(description, QgsTask.CanCancel)
        self.packages: List[PIPPackage] = packages
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


def checkGDALIssues() -> List[str]:
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


def requiredPackages(return_tuples: bool = False) -> List[PIPPackage]:
    """
    Returns a list of pip packages that should be installable according to the `requirements.csv` file
    :return: [list of strings]
    :rtype: list
    """

    # see https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
    # for details of requirements format

    file = REQUIREMENTS_CSV
    assert file.is_file(), '{} does not exist'.format(file)
    packages: List[PIPPackage] = []
    # rxPipPkg = re.compile(r'^[a-zA-Z_-][a-zA-Z0-9_-]*')

    with open(file, 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
        for row in reader:
            for k in list(row.keys()):
                if row[k] == '':
                    del row[k]

            pip_name = row['pip_name']
            pkg = PIPPackage(pip_name,
                             py_name=row.get('py_name', pip_name),
                             min_version=row.get('min_version'),
                             comment=row.get('comment'),
                             )

            packages.append(pkg)

    return packages


def missingPackages() -> List[PIPPackage]:
    """
    Returns missing packages
    :return: [PIPPackage]
    :rtype:
    """
    return [p for p in requiredPackages() if not p.isInstalled() and not p.skipStartupWarning()]


def missingPackageInfo(missing_packages: List[PIPPackage], html=True) -> str:
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

    info.append('</ol>')
    info.append('<p>Please follow the installation guide <a href="{0}">{0}</a><br/>'.format(URL_INSTALLATION))
    info.append('and install missing packages, e.g. with pip:<br/><br/>')

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
                if isinstance(m, Match):
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


class PIPPackageFilterModel(QSortFilterProxyModel):

    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)

        self.mFilter1 = 'required'

    def setPrimaryFilter(self, mode: str):
        assert mode in ['all', 'required', 'missing']
        self.mFilter1 = mode
        self.invalidateFilter()

    def primaryFilter(self):
        return self.mFilter1

    def filterAcceptsRow(self, sourceRow: int, sourceParent: QModelIndex):
        model = self.sourceModel()
        assert isinstance(model, PIPPackageInstallerTableModel)
        pkg = model.index(sourceRow, 0, sourceParent).data(Qt.UserRole)

        if isinstance(pkg, PIPPackage):
            is_required = pkg.pipPkgName in model.mIsEnMAPBoxRequirement
            is_missing = not pkg.isInstalled()
            if self.mFilter1 == 'required' and not is_required:
                return False
            elif self.mFilter1 == 'missing' and not (is_required and is_missing):
                return False

        return super().filterAcceptsRow(sourceRow, sourceParent)


class PIPPackageInstallerTableModel(QAbstractTableModel):
    CN_PIP = 0
    CN_VERSION = 1
    CN_LATEST_VERSION = 2
    CN_SUMMARY = 3
    CN_LOCATION = 4
    CN_LICENSE = 5
    CN_REQUIRES = 6

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.mColumnNames: dict = {
            self.CN_PIP: 'Package',
            self.CN_VERSION: 'Version',
            self.CN_LATEST_VERSION: 'Latest',
            self.CN_SUMMARY: 'Summary',
            self.CN_LOCATION: 'Location',
            self.CN_LICENSE: 'License',
            self.CN_REQUIRES: 'Requires'
        }

        self.mColumnToolTips: dict = {
            self.CN_PIP: 'PyPI package name',
            self.CN_VERSION: 'Installed Version',
            self.CN_LATEST_VERSION: 'Latest Version',
            self.CN_SUMMARY: 'Package Summary',
            self.CN_LOCATION: 'Install Location',
            self.CN_LICENSE: 'Package License',
            self.CN_REQUIRES: 'Requirements to use this package'
        }

        self.mPackages: List[PIPPackage] = []
        self.mPIP2Pkg: Dict[str, PIPPackage] = dict()
        self.mPy2Pkg: Dict[str, PIPPackage] = dict()

        self.mAnimatedIcon = QgsAnimatedIcon(QgsApplication.iconPath("/mIconLoading.gif"), self)

        self.mIsEnMAPBoxRequirement = set()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == self.CN_PIP:
            pkg = self.mPackages[index.row()]
            if pkg.pipPkgName in self.mIsEnMAPBoxRequirement:
                flags = flags | Qt.ItemIsUserCheckable
        return flags

    def setData(self, index: QModelIndex, value, role=None):
        if not index.isValid():
            return None

        pkg = self.mPackages[index.row()]

        assert isinstance(pkg, PIPPackage)
        col = index.column()
        cn = self.mColumnNames[col]

        changed = False
        if role == Qt.CheckStateRole:
            if col == self.CN_PIP:
                pkg.setWarnIfNotInstalled(value == Qt.Checked)
                changed = True

        if changed:
            idx0 = self.index(index.row(), 0, index.parent())
            idx1 = self.index(index.row(), self.columnCount() - 1, index.parent())
            self.dataChanged.emit(idx0, idx1, [role, Qt.ForegroundRole])
        return changed

    def updatePackages(self, updates: List[Dict[str, Any]]):
        new_packages = []
        for pkg_dict in updates:
            name = pkg_dict.get('name', pkg_dict.get('Name'))

            if name in self.mPIP2Pkg:
                pkg = self.mPIP2Pkg[name]
                pkg.updateFromDict(pkg_dict)
                idx = self.pkg2index(pkg)
                r = idx.row()
                self.dataChanged.emit(self.createIndex(r, 0),
                                      self.createIndex(r, self.columnCount() - 1))

            else:
                newPkg = PIPPackage.fromDict(pkg_dict)
                new_packages.append(newPkg)

        if len(new_packages) > 0:
            self.addPackages(new_packages)

    def __getitem__(self, slice):
        return self.mPackages[slice]

    def __contains__(self, item):
        return item in self.mPackages

    def __len__(self):
        return len(self.mPackages)

    def __iter__(self) -> Iterator[PIPPackage]:
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

    def data(self, index: QModelIndex, role: int = ...) -> Any:

        if not index.isValid():
            return None

        pkg = self.mPackages[index.row()]

        assert isinstance(pkg, PIPPackage)
        col = index.column()
        cn = self.mColumnNames[col]

        if role == Qt.DisplayRole:
            if col == self.CN_PIP:
                return pkg.pyPkgName

            if col == self.CN_VERSION:
                return pkg.version

            if col == self.CN_LATEST_VERSION:
                return pkg.version_latest

            if col == self.CN_SUMMARY:
                return pkg.summary

            if col == self.CN_LICENSE:
                return pkg.license

            if col == self.CN_LOCATION:
                return pkg.location

            if col == self.CN_REQUIRES:
                return pkg.requirements

            # if cn == self.cnCommand:
            #    cmd = pkg.installCommand(user=self.mUser, upgrade=pkg.mInstalledVersion < pkg.mLatestVersion)
            #    match = re.search(r'python(\.exe)?.*$', cmd, re.I)
            #    if match:
            #        return match.group()
            #    else:
            #        return cmd

        if role == Qt.ForegroundRole:
            if col == self.CN_VERSION:
                if not pkg.skipStartupWarning():
                    if pkg.version == '<not installed>':
                        return QColor('red')
                    else:
                        return QColor('green')
                elif pkg.version_latest > pkg.version:
                    return QColor('orange')

        if role == Qt.ToolTipRole:
            if col == self.CN_PIP:
                return self.mColumnNames[index.column()]

            # if cn == self.cnCommand:
            #    info = 'Command to install/update {} from your CLI.'.format(pkg.pyPkgName)
            #    if 'git+' in pkg.installCommand():
            #        info += '\nThis command requires having git (https://www.git-scm.com) installed!'
            #    return info

        if role == Qt.CheckStateRole:
            if col == self.CN_PIP and bool(self.flags(index) & Qt.ItemIsUserCheckable):
                return Qt.Unchecked if pkg.skipStartupWarning() else Qt.Checked

        # if role == Qt.DecorationRole and index.column() == 0:
        #    if pkg.version_latest == '<unknown>':
        #        return QIcon(':/images/themes/default/mIconLoading.gif')

        if role == Qt.UserRole:
            return pkg

    def addPackages(self, packages: List[PIPPackage], required: bool = False):

        for p in packages:
            assert isinstance(p, PIPPackage)

        if len(packages) > 0:
            n = self.rowCount()
            self.beginInsertRows(QModelIndex(), n, n + len(packages) - 1)
            for pkg in packages:
                self.mPIP2Pkg[pkg.pipPkgName] = pkg
                self.mPy2Pkg[pkg.pyPkgName] = pkg
            self.mPackages.extend(packages)
            if required:
                self.mIsEnMAPBoxRequirement.update([pkg.pipPkgName for pkg in packages])
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

        m = QMenu()
        a = m.addAction('Copy')
        a.setToolTip('Copies the cell value')
        a.triggered.connect(lambda *args, v=txt: QApplication.clipboard().setText(v))

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
        # self.proxyModel = QSortFilterProxyModel()
        self.proxyModel = PIPPackageFilterModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterKeyColumn(1)
        self.tableView.setModel(self.proxyModel)

        self.progressBar.setVisible(True)

        # self.cbUser.toggled.connect(self.model.setUser)
        self.rbAll.toggled.connect(lambda *args: self.updatePrimaryFilter())
        self.rbRequired.toggled.connect(lambda *args: self.updatePrimaryFilter())
        self.rbMissingOnly.toggled.connect(lambda *args: self.updatePrimaryFilter())
        self.tbFilter.textChanged.connect(self.updateTextFilter)
        self.proxyModel.setFilterKeyColumn(-1)
        self.updatePrimaryFilter()

        assert isinstance(self.tableView, PIPPackageInstallerTableView)
        self.tableView.setSortingEnabled(True)
        # self.tableView.sigInstallPackageRequest.connect(self.installPackages)
        self.tableView.sigPackageReloadRequest.connect(self.reloadPythonPackages)
        self.tableView.sortByColumn(1, Qt.DescendingOrder)
        # self.buttonBox.button(QDialogButtonBox.YesToAll).clicked.connect(self.installAll)
        self.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close)

        self.actionClearConsole.triggered.connect(self.tbLog.clear)
        self.actionCopyConsole.triggered.connect(
            lambda: QgsApplication.instance().clipboard().setText(self.tbLog.toPlainText()))
        self.btnClearConsole.setDefaultAction(self.actionClearConsole)
        self.btnCopyConsole.setDefaultAction(self.actionCopyConsole)

    def updateTextFilter(self, *args):
        txt = self.tbFilter.text().strip()
        if txt == '':
            self.proxyModel.setFilterWildcard('*')
        else:
            self.proxyModel.setFilterWildcard(txt)

    def updatePrimaryFilter(self):
        if self.rbRequired.isChecked():
            self.setPrimaryFilter('required')
        elif self.rbMissingOnly.isChecked():
            self.setPrimaryFilter('missing')
        else:
            self.setPrimaryFilter('all')

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
        warnings.warn(DeprecationWarning(), stacklevel=2)
        return
        self.installPackages([p for p in self.model if not p.isInstalled()])

    def installPackages(self, packages: List[PIPPackage]):
        warnings.warn(DeprecationWarning(), stacklevel=2)
        return

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

    def reloadPythonPackages(self, pipPackages: List[PIPPackage]):
        import importlib
        for pkg in pipPackages:
            try:
                module = __import__(pkg.pyPkgName)
                importlib.reload(module)
                info = '{} reloaded'.format(module)
                self.addText(info, True)
            except Exception as ex:
                self.addText(str(ex), True)

    def loadPIPVersionInfo(self, pipPackages: List[PIPPackage], load_latest_versions: bool = True):
        if len(pipPackages) == 0:
            pipPackages = self.model[:]
        else:
            for p in pipPackages:
                assert isinstance(p, PIPPackage)
        # get names
        pipPackageNames = [p.pipPkgName for p in pipPackages]

        task = PIPPackageInfoTask('Get package information')

        task.sigPackageList.connect(self.model.updatePackages)
        task.sigPackageUpdates.connect(self.model.updatePackages)
        task.sigPackageInfo.connect(self.model.updatePackages)
        self.startTask(task)

    def startTask(self, qgsTask: QgsTask):
        tid = id(qgsTask)

        qgsTask.progressChanged.connect(self.onProgressChanged)
        qgsTask.taskCompleted.connect(lambda *args, ti=tid: self.onRemoveTask(ti))
        qgsTask.taskTerminated.connect(lambda *args, ti=tid: self.onRemoveTask(ti))
        qgsTask.sigMessage.connect(self.onTaskMessage)
        self.mTasks[tid] = qgsTask
        if True:
            tm = QgsApplication.taskManager()
            assert isinstance(tm, QgsTaskManager)
            tm.addTask(qgsTask)
        else:
            qgsTask.run()

    def onTaskMessage(self, msg: str, msg_type: Qgis.MessageLevel):
        if msg_type in [Qgis.MessageLevel.Critical]:
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

    def setPrimaryFilter(self, mode: str):
        self.proxyModel.setPrimaryFilter(mode)

    def addText(self, text: str, color: QColor = None):

        c = self.tbLog.textColor()
        if isinstance(color, QColor):
            self.tbLog.setTextColor(color)
        self.tbLog.append(f'{datetime.datetime.now()}: {text}')
        self.tbLog.setTextColor(c)

    def addPackages(self, packages: List[PIPPackage], required: bool = False):
        self.model.addPackages(packages, required=required)
        self.loadPIPVersionInfo(packages)
