# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
import os
import pathlib
import shutil
import site
import sys

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'
__date__ = '2017-07-17'
__copyright__ = 'Copyright 2017, Benjamin Jakimow'

import unittest
from collections import namedtuple

from enmapbox.gui.applications import ApplicationRegistry
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QApplication, QAction, QWidget, QMenu

from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterDefinition, QgsProcessingParameterRasterLayer, \
    QgsApplication
from enmapbox import DIR_ENMAPBOX, DIR_REPO
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.gui.applications import EnMAPBoxApplication


class test_applications(EnMAPBoxTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        from enmapbox import DIR_ENMAPBOX
        site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'coreapps')
        site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'eo4qapps')
        site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'apps')
        site.addsitedir(pathlib.Path(DIR_ENMAPBOX) / 'apps' / 'lmuapps')

    def tearDown(self):

        app = QgsApplication.instance()
        if isinstance(app, QgsApplication):
            app.closeAllWindows()
        super().tearDown()

    def createTestData(self) -> (str, str, str):
        """
        :return: (path folder, filelist_abs, filelist_rel)
        """

        TESTDATA = namedtuple('TestData',
                              ['validAppDirs', 'invalidAppDirs', 'appDirs', 'pathListingAbs', 'pathListingRel'])

        DIR_TMP = self.createTestOutputDirectory() / 'AppTests'

        if os.path.isdir(DIR_TMP):
            shutil.rmtree(DIR_TMP)
        os.makedirs(DIR_TMP, exist_ok=True)

        TESTDATA.invalidAppDirs = []
        TESTDATA.validAppDirs = []

        # 1. valid app 1
        pAppDir = os.path.join(DIR_REPO, *['examples', 'minimumexample'])

        TESTDATA.validAppDirs.append(pAppDir)

        # 2. no app 1: empty directory
        pAppDir = os.path.join(DIR_TMP, 'NoApp1')
        os.makedirs(pAppDir)
        TESTDATA.invalidAppDirs.append(pAppDir)

        # 3. no app 2: __init__ without factory

        pAppDir = DIR_TMP / 'NoApp2'
        os.makedirs(pAppDir)
        pAppInit = pAppDir / '__init__.py'
        with open(pAppInit, 'w') as f:
            f.write('import sys')

        TESTDATA.invalidAppDirs.append(pAppDir)

        TESTDATA.pathListingAbs = DIR_TMP / 'application_abs.txt'
        with open(TESTDATA.pathListingAbs, 'w') as f:
            for p in TESTDATA.invalidAppDirs + TESTDATA.validAppDirs:
                f.write(f'{p}\n')

        TESTDATA.pathListingRel = DIR_TMP / 'application_rel.txt'
        with open(TESTDATA.pathListingRel, 'w') as f:
            for p in TESTDATA.invalidAppDirs + TESTDATA.validAppDirs:
                f.write(os.path.relpath(p, DIR_TMP) + '\n')

        return TESTDATA

    def test_application(self):
        EB = EnMAPBox()
        emptyApp = EnMAPBoxApplication(EB)

        isOk, errors = EnMAPBoxApplication.checkRequirements(emptyApp)
        self.assertFalse(isOk)
        self.assertIsInstance(errors, list)
        self.assertTrue(len(errors) > 0)
        self.assertIsInstance(emptyApp.processingAlgorithms(), list)
        self.assertEqual(len(emptyApp.processingAlgorithms()), 0)
        self.assertEqual(emptyApp.menu(QMenu), None)

        testApp = TestObjects.enmapboxApplication()

        isOk, errors = EnMAPBoxApplication.checkRequirements(testApp)
        self.assertTrue(isOk)
        self.assertIsInstance(errors, list)
        self.assertTrue(len(errors) == 0)
        self.assertIsInstance(testApp.processingAlgorithms(), list)
        self.assertTrue(len(testApp.processingAlgorithms()) > 0)
        self.assertIsInstance(testApp.menu(QMenu()), QMenu)

    def test_applicationRegistry(self):
        TESTDATA = self.createTestData()

        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)

        reg = ApplicationRegistry(EB)
        testApp = TestObjects.enmapboxApplication()
        self.assertIsInstance(reg.applications(), list)
        self.assertTrue(len(reg.applications()) == 0)

        app = TestObjects.enmapboxApplication()
        self.assertIsInstance(app, EnMAPBoxApplication)
        reg.addApplication(app)
        self.assertTrue(len(reg.applications()) == 1)
        self.assertTrue(len(reg.applications()) == len(reg))

        reg.removeApplication(app)
        self.assertTrue(len(reg.applications()) == 0)

        app2 = TestObjects.enmapboxApplication()
        reg.addApplication(app2)
        self.assertTrue(len(reg.applications()) == 1,
                        msg='Applications with same name are not allowed to be added twice')

        app2.name = 'TestApp2'
        reg.addApplication(app2)
        self.assertTrue(len(reg.applications()) == 2)

        reg.removeApplication(app2)
        self.assertTrue(len(reg.applications()) == 1, msg='Unable to remove application')

        # load a folder
        reg = ApplicationRegistry(EB)
        for d in TESTDATA.validAppDirs:
            self.assertTrue(reg.addApplicationFolder(d), msg='added {} returned False'.format(d))
        self.assertEqual(len(reg), len(TESTDATA.validAppDirs))

        reg = ApplicationRegistry(EB)
        for d in TESTDATA.invalidAppDirs:
            self.assertFalse(reg.addApplicationFolder(d))
        self.assertEqual(len(reg), 0)

        reg = ApplicationRegistry(EB)
        reg.addApplicationListing(TESTDATA.pathListingAbs)
        self.assertEqual(len(reg), len(TESTDATA.validAppDirs))

        reg = ApplicationRegistry(EB)
        reg.addApplicationListing(TESTDATA.pathListingRel)
        self.assertEqual(len(reg), len(TESTDATA.validAppDirs))

        reg = ApplicationRegistry(EB)
        reg.addApplicationListing(TESTDATA.pathListingAbs)
        reg.addApplicationListing(TESTDATA.pathListingRel)
        self.assertEqual(len(reg), len(TESTDATA.validAppDirs))

        reg = ApplicationRegistry(EB)
        rootFolder = os.path.dirname(TESTDATA.validAppDirs[0])
        reg.addApplicationFolder(rootFolder)
        self.assertTrue(len(reg) > 0, msg='Failed to add example EnMAPBoxApplication from {}'.format(rootFolder))

        print('finished')

    def test_IVVM(self):

        from lmuapps.lmuvegetationapps.IVVRM.IVVRM_GUI import MainUiFunc
        m = MainUiFunc()

        self.showGui(m)

    def test_deployed_apps(self):

        pathCoreApps = pathlib.Path(DIR_ENMAPBOX) / 'coreapps'
        pathEo4qApps = pathlib.Path(DIR_ENMAPBOX) / 'eo4qapps'
        pathExternalApps = pathlib.Path(DIR_ENMAPBOX) / 'apps'
        self.assertTrue(os.path.isdir(pathCoreApps))

        EB = EnMAPBox()
        reg = ApplicationRegistry(EB)

        coreAppDirs = []
        externalAppDirs = []

        for d in os.scandir(pathCoreApps):
            if d.is_dir():
                coreAppDirs.append(d.path)

        for d in os.scandir(pathEo4qApps):
            if d.is_dir():
                coreAppDirs.append(d.path)

        for d in os.scandir(pathExternalApps):
            if d.is_dir():
                externalAppDirs.append(d.path)

        print('Load APP(s) from {}...'.format(pathExternalApps))
        for d in coreAppDirs + externalAppDirs:
            n1 = len(reg)
            reg.addApplicationFolder(d)
            n2 = len(reg)
            if n1 == n2:
                print('Unable to add EnMAPBoxApplications from {}'.format(d), file=sys.stderr)

        EB.close()

    def closeBlockingDialogs(self):
        w = QApplication.instance().activeModalWidget()
        if isinstance(w, QWidget):
            print('Close blocking {} "{}"'.format(w.__class__.__name__, w.windowTitle()))
            w.close()

    def test_enmapbox_start(self):

        timer = QTimer()
        timer.timeout.connect(self.closeBlockingDialogs)
        timer.start(1000)

        EB = EnMAPBox()

        titles = [m.title() for m in EB.ui.menuBar().children() if isinstance(m, QMenu)]
        print('Menu titles: {}'.format(','.join(titles)))

        # calls all QMenu actions
        def triggerActions(menuItem, prefix=''):
            if isinstance(menuItem, QAction):
                print('Trigger QAction {}"{}" {}'.format(prefix, menuItem.text(), menuItem.toolTip()))
                menuItem.trigger()
                QApplication.processEvents()
            elif isinstance(menuItem, QMenu):
                for a in menuItem.actions():
                    triggerActions(a, prefix='"{}"->'.format(menuItem.title()))
                    QApplication.processEvents()

        for title in ['Tools', 'Applications']:
            print('## TEST QMenu "{}"'.format(title))

            triggerActions(EB.menu(title))
            QApplication.processEvents()

        self.showGui()


if __name__ == "__main__":
    unittest.main(buffer=False)


class ExampleParameterDefinition(QgsProcessingParameterDefinition):

    def __init__(self, name='', description='', ext='bsq'):
        QgsProcessingParameterDefinition.__init__(self, name, description)
        self.ext = ext

    def getFileFilter(self, alg):
        if self.ext is None:
            return self.tr('ENVI (*.bsq *.bil);;TIFF (*.tif);;All files(*.*)', 'OutputFile')
        else:
            return self.tr('%s files(*.%s)', 'OutputFile') % (self.ext, self.ext)

    def getDefaultFileExtension(self, alg):

        return 'bsq'


class ExampleProcessingAlgorithm(QgsProcessingAlgorithm):

    def defineCharacteristics(self):
        self.name = 'TestAlgorithm'
        self.group = 'TestGroup'
        # self.addParameter(ParameterRaster('infile', 'Test Input Image'))
        self.addOutput(QgsProcessingParameterRasterLayer('outfile1', 'Test Output Image'))
        self.addOutput(ExampleParameterDefinition('outfile2', 'Test MyOutput Image'))

    def processAlgorithm(self, progress):
        # map processing framework parameters to that of you algorithm
        infile = self.getParameterValue('infile')
        outfile = self.getOutputValue('outfile')
        outfile2 = self.getOutputValue('outfile2')
        s = ""
        # define
        # todo:

    def help(self):
        return True, '<todo: describe test>'


class ExampleApplication(EnMAPBoxApplication):

    def __init__(self, enmapbBox):
        super(EnMAPBoxApplication, self).__init__(enmapbBox)

        self.name = 'Test'
        self.version = '0.8.15'
        self.licence = 'None'

    def menu(self, appMenu):
        assert isinstance(appMenu, QMenu)
        a = appMenu.addAction('Call dummy action')
        a.triggered.connect(self.dummySlot)

    def processingAlgorithms(self):
        return [ExampleProcessingAlgorithm()]

    def dummySlot(self, *arg, **kwds):
        print('Dummy Slot called.')
