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
import csv
import datetime
import enum
import importlib.util
import json
import logging
import os
import platform
import re
import subprocess
import sys
import time
import traceback
import typing
from importlib.machinery import ModuleSpec
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterator, List, Match, Optional, Tuple

from enmapbox import REQUIREMENTS_CSV
from enmapbox.enmapboxsettings import EnMAPBoxSettings
from enmapbox.qgispluginsupport.qps.utils import qgisAppQgisInterface
from qgis.PyQt import sip
from qgis.PyQt.QtCore import pyqtSignal, QAbstractTableModel, QModelIndex, QProcess, QSortFilterProxyModel, Qt, QUrl
from qgis.PyQt.QtGui import QColor, QContextMenuEvent, QDesktopServices
from qgis.PyQt.QtWidgets import QApplication, QDialogButtonBox, QMenu, QMessageBox, QStyledItemDelegate, QTableView, \
    QWidget
from qgis.core import Qgis, QgsAnimatedIcon, QgsApplication, QgsTask, QgsTaskManager
from qgis.gui import QgsFileDownloaderDialog

logger = logging.getLogger(__name__)

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
    """
    Describes a single python package that can be installed via pip.
    """

    @staticmethod
    def fromDict(info) -> Optional['PIPPackage']:
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
                 required_by: Optional[str] = None,
                 min_version: str = None,
                 used_by: List[str] = None,
                 comment: str = None):

        assert isinstance(pip_name, str)
        assert len(pip_name) > 0
        pip_name = pip_name.strip()
        if py_name is None:
            py_name = PACKAGE_LOOKUP.get(pip_name, pip_name)

        if py_name is None:
            s = ""
        self.pyPkgName: str = py_name
        self.pipPkgName = pip_name
        self.required_by: Optional[str] = required_by
        self.mIsInstalled: Optional[bool] = None
        self.installer: str = ''
        self.location: str = ''
        self.stderrMsg: str = ''
        self.stdoutMsg: str = ''

        self.version_latest: str = ''
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

    def isCoreRequirement(self) -> bool:
        return self.required_by == 'core'

    def __repr__(self):
        return super().__repr__() + f'"{self.pipPkgName}"'

    def updateFromDict(self, info: dict):
        info = {k.lower(): v for k, v in info.items()}
        assert 'name' in info
        assert info['name'] == self.pipPkgName

        if 'version' in info:
            self.version = info['version']
            if self.version_latest == '':
                self.version_latest = self.version

        if 'required_by' in info:
            self.required_by = info['required_by']

        if 'summary' in info:
            self.summary = info['summary']

        if 'location' in info:
            if self.location == '':
                self.location = info['location']

        if 'installer' in info:
            self.installer = info['installer']

        if 'license' in info:
            self.license = info['license']

        if 'requires' in info:
            self.requirements = info['requires']

        if 'home-page' in info:
            url = info['home-page']
            self.homepage = url

        if 'latest_version' in info:
            self.version_latest = info['latest_version']

        self.mIsInstalled = None
        s = ""

    def isMissing(self) -> bool:
        return not self.isInstalled()

    def updateAvailable(self) -> bool:
        return self.version < self.version_latest

    KEY_SKIP_WARNINGS = 'PIPInstaller/SkipWarnings'

    def packagesWithoutWarning(self) -> List[str]:
        return EnMAPBoxSettings().value(self.KEY_SKIP_WARNINGS, defaultValue='', type=str).split(',')

    def skipStartupWarning(self) -> bool:
        return self.pipPkgName in self.packagesWithoutWarning()

    def setWarnIfNotInstalled(self, b: bool = True):
        noWarning = self.packagesWithoutWarning()
        if b and self.pipPkgName in noWarning:
            noWarning.remove(self.pipPkgName)
        elif not b and self.pipPkgName not in noWarning:
            noWarning.append(self.pipPkgName)
        noWarning = [p for p in noWarning if isinstance(p, str)]
        EnMAPBoxSettings().setValue(self.KEY_SKIP_WARNINGS, ','.join(noWarning))

    def __str__(self):
        return '{}'.format(self.pyPkgName)

    def __eq__(self, other):
        if not isinstance(other, PIPPackage):
            return False
        return self.pyPkgName == other.pyPkgName

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

    def isInstalled(self) -> bool:
        """
        Returns True if the package is installed and can be imported in python
        :return:
        :rtype:
        """

        if not isinstance(self.mIsInstalled, bool):
            if self.location != '':
                # the pip package name was found by pip
                self.mIsInstalled = True
            elif isinstance(self.pyPkgName, str):
                # we can import it with python
                try:
                    spam_spec = importlib.util.find_spec(self.pyPkgName)
                    if isinstance(spam_spec, ModuleSpec) and spam_spec.has_location:
                        self.location = os.path.dirname(spam_spec.origin)
                    self.mIsInstalled = spam_spec is not None
                except Exception as ex:
                    # https://github.com/EnMAP-Box/enmap-box/issues/215
                    self.mError = str(ex)

        return self.mIsInstalled is True


_LOCAL_PIPEXE: Optional[Path] = None


def get_prog() -> str:
    try:
        prog = os.path.basename(sys.argv[0])
        if prog in ("__main__.py", "-c"):
            return f"{sys.executable} -m pip"
        else:
            return prog
    except (AttributeError, TypeError, IndexError):
        pass
    return "pip"


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
                    msgOut = decode_bytes(process.readAllStandardOutput().data())
                    msgErr = decode_bytes(process.readAllStandardError().data())
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


def localPythonExecutable() -> Optional[Path]:
    """
    Searches for the local python executable
    :return:
    """
    candidates = [Path(sys.executable)]
    pythonhome = os.environ.get('PYTHONHOME', None)
    if pythonhome:
        pythonhome = Path(pythonhome)
        ext = ''
        if 'windows' in platform.uname().system.lower():
            ext = '.exe'
        for n in ['python3', 'python']:
            candidates.extend([
                pythonhome / f'{n}{ext}',
                pythonhome / 'bin' / f'{n}{ext}'
            ])

    for c in candidates:
        c = Path(c.resolve())
        if c.is_file() and 'python' in c.name.lower():
            return c

    return None


def decode_bytes(bytes_str, encodings=None):
    if encodings is None:
        encodings = ['utf-8', 'latin-1', 'ascii']
    for encoding in encodings:
        try:
            return bytes_str.decode(encoding)
        except ValueError:
            continue
    # If all encodings fail, return None or handle the error as needed
    return None


def call_pip_command(pipArgs) -> Tuple[bool, Optional[str], Optional[str]]:
    assert isinstance(pipArgs, list)

    success = 0
    msgOut = msgErr = None
    if True:
        pipexe = localPipExecutable()
        cmd = [str(pipexe)] + pipArgs

        kwargs = {}
        if sys.platform == "win32":
            # Prevent opening a console window
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                **kwargs,
                                )
        success = result.returncode == 0
        msgOut = result.stdout
        msgErr = result.stderr
        if success:
            return success, msgOut, msgErr

    if False:
        pipexe = localPipExecutable()
        process = QProcess()
        process.readyRead()
        process.start(f'{pipexe}' + ' '.join(pipArgs))
        process.waitForFinished()

        msgOut = decode_bytes(process.readAllStandardOutput().data())
        msgErr = decode_bytes(process.readAllStandardError().data())
        success = process.exitCode() == 0
        if success or msgErr != '':
            return success, msgOut.replace('\r\n', '\n'), msgErr.replace('\r\n', '\n')

    if True:
        _std_out = sys.stdout
        _std_err = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        msgOut = None
        msgErr = None
        success = False
        try:
            from pip._internal.cli.main_parser import parse_command
            from pip._internal.commands import create_command

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

    if msgOut:
        msgOut.replace('\r\n', '\n')

    if msgErr:
        msgErr.replace('\r\n', '\n')

    return success, msgOut, msgErr


class PIPPackageInfoTask(QgsTask):
    sigMessage = pyqtSignal(str, Qgis.MessageLevel)

    sigPackageList = pyqtSignal(list)
    sigPackageUpdates = pyqtSignal(list)
    sigPackageInfo = pyqtSignal(list)

    def __init__(self, description: str = 'Update PyPI Status',
                 packages_of_interest=None,
                 batch_size: int = 20,
                 poi_only: bool = False,
                 search_updates: bool = True,
                 search_info: bool = True,
                 callback=None):
        super().__init__(description, QgsTask.CanCancel)

        if packages_of_interest is None:
            packages_of_interest = []
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
            success, msg, err = call_pip_command(['list', '-v', '--format', 'json'])
            if success and msg not in ['', None]:
                pkg_all = json.loads(msg)

                pkg_names = [pkg['name'] for pkg in pkg_all]
                for name in self._pois:
                    if name not in pkg_names:
                        pkg_all.append({'name': name})

                self.sigPackageList.emit(pkg_all)
            else:
                self.sigMessage.emit(err, Qgis.MessageLevel.Critical)
                return False
            self._messages['list'] = (success, msg, err)
        except Exception as ex:
            err = str(ex)
            self._messages['list_err'] = (False, msg, err)
            errInfo = str(ex) + '\n' + traceback.format_exc()
            self.sigMessage.emit(errInfo, Qgis.MessageLevel.Critical)
            return False
        self.setProgress(10)

        if self.isCanceled():
            return False

        msg = err = ''
        if isinstance(pkg_all, list) and self._search_updates:
            self.sigMessage.emit('Search for available updates...', Qgis.MessageLevel.Info)
            try:
                success, msg, err = call_pip_command(['list', '-o', '--format', 'json'])

                if success and msg not in ['', None]:
                    pkg_updates = json.loads(msg)
                    self.sigPackageUpdates.emit(pkg_updates)
                else:
                    self.sigMessage.emit(err, Qgis.MessageLevel.Critical)
                    return False

                self._messages['updates'] = (success, msg, err)
            except Exception as ex:
                errInfo = str(ex) + '\n' + traceback.format_exc()
                self._messages['updates'] = (False, msg, err)
                self.sigMessage.emit(errInfo, Qgis.MessageLevel.Critical)
                return False

        self.setProgress(20)
        if self.isCanceled():
            return False

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

                    if self.isCanceled():
                        return False

            except Exception as ex:
                errInfo = str(ex) + '\n' + traceback.format_exc()
                self.sigMessage.emit(errInfo, Qgis.MessageLevel.Critical)
                self._messages['major_exception'] = errInfo
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


def checkGDALIssues() -> List[str]:
    """
    Tests for known GDAL issues
    :return: list of errors / known problems
    """
    from osgeo import gdal
    issues = []
    drv = gdal.GetDriverByName('GPKG')

    if not isinstance(drv, gdal.Driver):
        info = 'GDAL/OGR installation does not support the GeoPackage (GPKG) vector driver'
        info += '(https://gdal.org/drivers/vector/gpkg.html).\n'
        issues.append(info)
    return issues


def requiredPackages(return_tuples: bool = False) -> List[PIPPackage]:
    """
    Returns a list of pip packages that should be installable, according to the `requirements.csv` file
    :return: [list of strings]
    :rtype: list
    """

    # see https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
    # for details of the requirements format

    file = REQUIREMENTS_CSV
    assert file.is_file(), '{} does not exist'.format(file)
    packages: List[PIPPackage] = []
    # rxPipPkg = re.compile(r'^[a-zA-Z_-][a-zA-Z0-9_-]*')

    with open(file, 'r', newline='') as csv_file:
        lines = [l.strip() for l in csv_file.read().splitlines()]
        lines = [l for l in lines if not l.startswith('#')]
        reader = csv.DictReader(lines, delimiter=',', quotechar='"')
        for row in reader:
            for k in list(row.keys()):
                if row[k] == '':
                    del row[k]

            pip_name = row['pip_name']
            required_by = row.get('required_by', None)
            if required_by:
                s = ""
            pkg = PIPPackage(pip_name,
                             required_by=required_by,
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
        return ''

    from enmapbox import URL_INSTALLATION
    info = ['The following {} package(s) are not installed:'.format(n), '<ol>']
    for i, pkg in enumerate(missing_packages):
        assert isinstance(pkg, PIPPackage)
        info.append(f'\t<li>{pkg.pyPkgName} (pip install {pkg.pipPkgName})</li>')

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
    if ask:
        btn = QMessageBox.question(None,
                                   'Testdata is missing or outdated',
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

        targetDir = Path(DIR_EXAMPLEDATA)
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
                    subPaths.append(Path(m.group(1)))

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
            if self.mFilter1 == 'required':
                if pkg.required_by is None:
                    return False
                else:
                    s = ""
            elif self.mFilter1 == 'missing':
                if pkg.required_by is None:
                    return False
                if pkg.isInstalled():
                    return False

        result = super().filterAcceptsRow(sourceRow, sourceParent)
        return result


class PIPPackageInstallerTableModel(QAbstractTableModel):
    CN_PIP = 0
    CN_VERSION = 1
    CN_LATEST_VERSION = 2
    CN_SUMMARY = 3
    CN_LOCATION = 4
    CN_INSTALLER = 5
    CN_LICENSE = 6
    CN_HOMEPAGE = 7
    CN_REQUIRES = 8

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.mColumnNames: dict = {
            self.CN_PIP: 'Package',
            self.CN_VERSION: 'Version',
            self.CN_LATEST_VERSION: 'Latest',
            self.CN_SUMMARY: 'Summary',
            self.CN_LOCATION: 'Location',
            self.CN_INSTALLER: 'Installer',
            self.CN_LICENSE: 'License',
            self.CN_REQUIRES: 'Requires',
            self.CN_HOMEPAGE: 'Homepage',
        }

        self.mColumnToolTips: dict = {
            self.CN_PIP: 'PyPI package name. <br>Uncheck to skip a "missing package" warning at EnMAP-Box startup.',
            self.CN_VERSION: 'Installed Version',
            self.CN_LATEST_VERSION: 'Latest Version',
            self.CN_SUMMARY: 'Package Summary',
            self.CN_LOCATION: 'Install Location',
            self.CN_INSTALLER: 'The installer that installed the package',
            self.CN_LICENSE: 'Package License',
            self.CN_REQUIRES: 'Requirements to use this package',
            self.CN_HOMEPAGE: 'Package Homepage with further details',
        }

        self.mPackages: List[PIPPackage] = []
        self.mPIP2Pkg: Dict[str, PIPPackage] = dict()
        self.mPy2Pkg: Dict[str, PIPPackage] = dict()

        self.mAnimatedIcon = QgsAnimatedIcon(QgsApplication.iconPath("/mIconLoading.gif"), self)

        # self.mIsEnMAPBoxRequirement = set()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == self.CN_PIP:
            pkg = self.mPackages[index.row()]
            if pkg.isCoreRequirement() and pkg.isMissing():
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

    def updatePackages(self, updates: List[Dict[str, Any]]) -> Tuple[List[PIPPackage], List[PIPPackage]]:

        updated_packages = []
        new_packages = []
        n_updated = 0

        for pkg_dict in updates:
            name = pkg_dict.get('name', pkg_dict.get('Name'))

            if name in self.mPIP2Pkg:
                pkg = self.mPIP2Pkg[name]
                pkg.updateFromDict(pkg_dict)
                idx = self.pkg2index(pkg)
                r = idx.row()
                self.dataChanged.emit(self.createIndex(r, 0),
                                      self.createIndex(r, self.columnCount() - 1))
                updated_packages.append(pkg)
                n_updated += 1
            else:
                newPkg = PIPPackage.fromDict(pkg_dict)
                new_packages.append(newPkg)

        if len(new_packages) > 0:
            self.addPackages(new_packages)

        return updated_packages, new_packages

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

    def htmlToolTip(self, package: PIPPackage) -> str:
        assert isinstance(package, PIPPackage)

        html = f'<b>PyPi Package:</b> {package.pipPkgName}'
        if isinstance(package.pyPkgName, str) and package.pipPkgName != package.pyPkgName:
            html += f'<br> import as: <code>import {package.pyPkgName}</code>'

        pkg_license = package.license.splitlines()[0] if len(package.license) > 0 else ''

        html += f"""<br>
        <b>Summary:</b>{package.summary}<br>
        <b>Installed Version:</b> {package.version}<br>
        <b>Latest Version:</b> {package.version_latest}<br>
        <b>Homepage:</b> <a href="{package.homepage}">{package.homepage}</a><br>
        <b>Licence:</b> {pkg_license}<br>
        <b>Requires:</b> {package.requirements}<br>
        """
        return html

    def data(self, index: QModelIndex, role: int = ...) -> Any:

        if not index.isValid():
            return None

        pkg = self.mPackages[index.row()]

        assert isinstance(pkg, PIPPackage)
        col = index.column()
        cn = self.mColumnNames[col]

        if role == Qt.DisplayRole:
            if col == self.CN_PIP:
                return pkg.pipPkgName

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

            if col == self.CN_INSTALLER:
                return pkg.installer

            if col == self.CN_REQUIRES:
                return pkg.requirements

            if col == self.CN_HOMEPAGE:
                return pkg.homepage
            # if cn == self.cnCommand:
            #    cmd = pkg.installCommand(user=self.mUser, upgrade=pkg.mInstalledVersion < pkg.mLatestVersion)
            #    match = re.search(r'python(\.exe)?.*$', cmd, re.I)
            #    if match:
            #        return match.group()
            #    else:
            #        return cmd

        if role == Qt.BackgroundRole:
            if pkg.isCoreRequirement() and not pkg.skipStartupWarning() and pkg.isMissing():
                # #FFC800 = color used for warnings in QgsMessageBar
                return QColor('#FFC800')

        if role == Qt.ToolTipRole:
            if col in [self.CN_PIP, self.CN_VERSION, self.CN_LATEST_VERSION]:
                return self.htmlToolTip(pkg)
            elif col == self.CN_HOMEPAGE:
                if len(pkg.homepage) > 0:
                    return f'<a href="{pkg.homepage}">{pkg.homepage}</a>'
            else:
                return self.data(index, Qt.DisplayRole)

        if role == Qt.CheckStateRole:
            if col == self.CN_PIP and bool(self.flags(index) & Qt.ItemIsUserCheckable):
                return Qt.Unchecked if pkg.skipStartupWarning() else Qt.Checked

        if role == Qt.UserRole:
            return pkg

    def addPackages(self, packages: List[PIPPackage]):

        for p in packages:
            assert isinstance(p, PIPPackage)

        if len(packages) > 0:
            n = self.rowCount()
            self.beginInsertRows(QModelIndex(), n, n + len(packages) - 1)
            for pkg in packages:
                self.mPIP2Pkg[pkg.pipPkgName] = pkg
                self.mPy2Pkg[pkg.pyPkgName] = pkg
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

        m = QMenu()
        a = m.addAction('Copy')
        a.setToolTip('Copy the cell value')
        a.triggered.connect(lambda *args, v=txt: QApplication.clipboard().setText(v))

        a = m.addAction('Open location')
        a.setToolTip(f'Open the installation folder of {pkg.pipPkgName}')
        a.setEnabled(pkg.location != '')
        a.triggered.connect(lambda *args, path=pkg.location: QDesktopServices.openUrl(QUrl.fromLocalFile(path)))

        a = m.addAction('Open homepage')
        a.setToolTip(f'Open the "{pkg.pipPkgName}" homepage')
        a.setEnabled(pkg.homepage != '')
        a.triggered.connect(lambda *args, url=pkg.homepage: QDesktopServices.openUrl(QUrl.fromUserInput(url)))
        m.exec_(event.globalPos())


class PIPPackageInstaller(QWidget):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        from enmapbox.gui.utils import loadUi
        from enmapbox import DIR_UIFILES
        path = Path(DIR_UIFILES) / 'pippackageinstaller.ui'
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
        p = int(progress)
        self.progressBar.setValue(p)

    def onCompleted(self, result: bool, task: QgsTask):
        if isinstance(task, PIPPackageInfoTask) and not sip.isdeleted(task):
            self.onRemoveTask(id(task))

        self.progressBar.setValue(0)

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
        s = ""

    def loadPIPVersionInfo(self, pipPackages: List[PIPPackage], load_latest_versions: bool = True):
        if len(pipPackages) == 0:
            pipPackages = self.model[:]
        else:
            for p in pipPackages:
                assert isinstance(p, PIPPackage)
        # get names
        pipPackageNames = [p.pipPkgName for p in pipPackages]

        task = PIPPackageInfoTask('Get package information', callback=self.onCompleted)

        task.sigPackageList.connect(lambda *args: self.receivePackageList(*args, prefix='Loaded package overview'))
        task.sigPackageUpdates.connect(lambda *args: self.receivePackageList(*args, prefix='Fetched available updates'))
        task.sigPackageInfo.connect(lambda *args: self.receivePackageList(*args, prefix='Fetched package details'))
        self.startTask(task)

    def receivePackageList(self, *args, prefix: str = 'Refreshed packages'):
        updated, newpackages = self.model.updatePackages(*args)

        pkgNames = [pkg.pipPkgName for pkg in updated + newpackages]

        text = f'{prefix} ({len(pkgNames)}): ' + ','.join(pkgNames)

        self.addText(text, Qgis.MessageLevel.Success)

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
        n = self.proxyModel.rowCount()
        s = ""

    def addText(self, text: str, color: QColor = None):

        c = self.tbLog.textColor()
        if isinstance(color, QColor):
            self.tbLog.setTextColor(color)
        self.tbLog.append(f'{datetime.datetime.now().strftime("%H:%M:%S")}: {text}')
        self.tbLog.setTextColor(c)

    def addPackages(self, packages: List[PIPPackage]):
        self.model.addPackages(packages)
        self.loadPIPVersionInfo(packages)
