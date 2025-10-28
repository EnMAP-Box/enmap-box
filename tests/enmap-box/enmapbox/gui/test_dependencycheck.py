# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'
__date__ = '2017-07-17'
__copyright__ = 'Copyright 2017, Benjamin Jakimow'

import os
import pathlib
import sys
import unittest
import uuid
from time import sleep
from typing import List, Tuple

from enmapbox.dependencycheck import PIPPackage, requiredPackages, PIPPackageInstaller, PIPPackageInfoTask, \
    localPythonExecutable, missingPackageInfo, checkGDALIssues, PIPPackageInstallerTableModel, \
    call_pip_command, localPipExecutable
from enmapbox.testing import EnMAPBoxTestCase, start_app
from qgis.PyQt.QtCore import QProcess
from qgis.PyQt.QtGui import QMovie
from qgis.PyQt.QtWidgets import QApplication, QTableView, QLabel
from qgis.core import Qgis, QgsTaskManager, QgsTask
from qgis.core import QgsApplication

start_app()


# @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'Skipped, takes too much time')
class test_dependencycheck(EnMAPBoxTestCase):

    def test_gdalissues(self):
        issues = checkGDALIssues()
        self.assertIsInstance(issues, list)
        for i in issues:
            self.assertIsInstance(i, str)

    def test_pip_call(self):

        pip_exe = localPipExecutable()
        self.assertTrue(os.path.isfile(pip_exe))

        process = QProcess()
        process.start(f'{pip_exe} show numpy')
        process.waitForFinished()
        msgOut = process.readAllStandardOutput().data().decode('utf-8')
        msgErr = process.readAllStandardError().data().decode('utf-8')
        success = process.exitCode() == 0
        self.assertTrue(success)
        self.assertTrue(msgOut.startswith('Name: numpy'))
        s = ""

    def test_required_packages(self):

        for p in requiredPackages():
            self.assertIsInstance(p, PIPPackage)

    def test_lookup(self):
        # some python packages have a different name when to be installed with pip
        # addresses https://bitbucket.org/hu-geomatics/enmap-box/issues/307/installation-problem-sklearn

        pipName = self.nonexistingPackageName()
        pyName = pipName.replace('-', '_')

        info = missingPackageInfo([PIPPackage(pipName, py_name=pyName)])
        self.assertTrue(pyName in info)
        self.assertTrue(pipName in info)

    def test_pippackage(self):
        pkg = PIPPackage('GDAL', py_name='osgeo.gdal')

        self.assertTrue(pkg.isInstalled())
        self.assertIsInstance(pkg.installCommand(), str)
        pkg.installPackage()

        pkg = PIPPackage(self.nonexistingPackageName())
        self.assertFalse(pkg.isInstalled())
        self.assertIsInstance(pkg.installCommand(), str)

    def test_pippackagemodel(self):
        model = PIPPackageInstallerTableModel()
        # tester = QAbstractItemModelTester(model, QAbstractItemModelTester.FailureReportingMode.Fatal)
        self.assertTrue(len(model) == 0)

        model.addPackages([PIPPackage(self.nonexistingPackageName()),
                           PIPPackage('gdal')]
                          )

        self.assertEqual(len(model), 2)
        self.assertEqual(model.rowCount(), 2)

        tv = QTableView()
        tv.setModel(model)

        self.showGui(tv)

    def nonexistingPackageName(self) -> str:
        s = str(uuid.uuid4())
        return 'foobar' + s

    def test_PIPInstallerTableModel(self):

        model = PIPPackageInstallerTableModel()
        # tester = QAbstractItemModelTester(model, QAbstractItemModelTester.FailureReportingMode.Fatal)

        pkgs = requiredPackages()
        model.addPackages(pkgs)
        model.updatePackages([{'Name': 'foobar', 'Version': '0815'}])

        pois = [p.pipPkgName for p in pkgs]
        task = PIPPackageInfoTask(packages_of_interest=pois, poi_only=False)
        task.sigPackageList.connect(model.updatePackages)
        task.sigPackageUpdates.connect(model.updatePackages)
        task.sigPackageInfo.connect(model.updatePackages)
        task.run()

        tv = QTableView()
        tv.setModel(model)

        self.showGui(tv)

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'Skipped, would take too long')
    def test_PIPInstaller(self):
        pkgs = [PIPPackage(self.nonexistingPackageName()),
                PIPPackage(self.nonexistingPackageName()),
                PIPPackage(self.nonexistingPackageName())]
        pkgs += requiredPackages()
        w = PIPPackageInstaller()

        w.addPackages(pkgs, required=True)
        # w.installAll()
        # w.model.installAll()

        self.showGui(w)

    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'Skipped, demo only')
    def test_AnimatedIcon(self):
        label = QLabel()
        p = QgsApplication.iconPath("/mIconLoading.gif")
        # icon = QIcon(p)
        # pm = icon.pixmap(QSize(50,50))
        # label.setPixmap(pm)
        movie = QMovie(p)
        movie.start()
        label.setMovie(movie)
        self.showGui(label)

    def test_PIPPackageInfoTask(self):
        required = [PIPPackage(self.nonexistingPackageName())] + requiredPackages()
        ALL_PKG: dict = dict()
        PKG_UPDATES: dict = dict()
        PKG_INFOS: List[Tuple[str, dict]] = []
        last_progress = -1
        is_completed = False

        def onPackageList(info: list):
            for p in info:
                ALL_PKG[p['name']] = p

        def onPackageUpdates(info: list):
            for p in info:
                ALL_PKG[p['name']].update(p)

        def onPackageInfo(infoBadge: list):
            self.assertIsInstance(infoBadge, list)
            self.assertTrue(len(infoBadge) > 0)
            for info in infoBadge:
                self.assertIsInstance(info, dict)
                self.assertTrue('Name' in info)

                for k in ['Name', 'Version']:
                    if k not in info:
                        s = ""
                    self.assertTrue(k in info.keys())
                    value = info[k]
                    self.assertIsInstance(value, str)
                    self.assertEqual(value, value.strip())

            PKG_INFOS.extend(infoBadge)
            s = ""

        def onProgress(p: int):
            print('Progress {}'.format(p))
            nonlocal last_progress
            last_progress = p

        MESSAGE_LEVEL = {
            Qgis.MessageLevel.Info: 'INFO',
            Qgis.MessageLevel.Critical: 'CRITICAL',
            Qgis.MessageLevel.Warning: 'WARNING',
            Qgis.MessageLevel.Success: 'SUCCESS',
            Qgis.MessageLevel.NoLevel: '<no level>',
        }

        def onMessage(msg: str, msg_level: Qgis.MessageLevel):
            self.assertIsInstance(msg, str)
            self.assertIsInstance(msg_level, Qgis.MessageLevel)
            self.assertTrue(len(msg) > 0)

        def onCompleted(result, task):
            nonlocal is_completed
            self.assertTrue(result)
            is_completed = True
            s = ""

        pois = [p.pipPkgName for p in requiredPackages()]
        task = PIPPackageInfoTask('package info',
                                  packages_of_interest=pois,
                                  poi_only=True,
                                  search_info=not EnMAPBoxTestCase.runsInCI(),
                                  search_updates=True,
                                  callback=onCompleted)

        task.progressChanged.connect(onProgress)
        task.sigPackageList.connect(onPackageList)
        task.sigPackageUpdates.connect(onPackageUpdates)
        task.sigPackageInfo.connect(onPackageInfo)
        task.sigMessage.connect(onMessage)

        if False:
            # run with QgsTaskManager
            tm = QgsApplication.taskManager()
            assert isinstance(tm, QgsTaskManager)
            tm.addTask(task)
            while task.status() != QgsTask.TaskStatus.Complete:
                QApplication.processEvents()
                sleep(0.2)
        else:
            # run in same process
            task.finished(task.run())

        if not EnMAPBoxTestCase.runsInCI():
            PKG_INFOS = {p['Name']: p for p in PKG_INFOS}
            for k in ['numpy', 'GDAL', 'scikit-learn']:
                self.assertTrue(k in PKG_INFOS, msg=f'Missing package info for {k}')
            self.assertTrue(last_progress == 100)
            self.assertTrue(is_completed)

    def test_call_pip_command(self):
        # python.exe -m pip list'

        stdout = sys.stdout
        stderr = sys.stderr
        success, msg, err = call_pip_command(['list'])
        self.assertTrue(success)
        self.assertEqual(stdout, sys.stdout)
        self.assertEqual(stderr, sys.stderr)

        success, msg, err = call_pip_command(['foobar'])
        self.assertFalse(success)
        self.assertEqual(stdout, sys.stdout)
        self.assertEqual(stderr, sys.stderr)

        s = ""

    def test_findpython(self):
        p = localPythonExecutable()
        self.assertIsInstance(p, pathlib.Path)
        self.assertTrue(p.is_file())
        self.assertTrue('python' in p.name.lower())

        import subprocess
        cmd = str(p) + ' --version'

        process = subprocess.run(cmd,
                                 check=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 universal_newlines=True)
        self.assertTrue(process.stdout.startswith('Python 3.'))


if __name__ == "__main__":
    unittest.main(buffer=False)
