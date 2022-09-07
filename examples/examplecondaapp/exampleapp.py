# -*- coding: utf-8 -*-

"""
***************************************************************************
    minimumexample/exampleapp.py

    This module defines the interactions between an application and
    the EnMAPBox.
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

import os

from examples.exampleapp.enmapboxintegration import ExampleEnMAPBoxApp
from qgis.PyQt.QtCore import QProcess, QProcessEnvironment
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction, QWidget, QVBoxLayout, QFrame, QGridLayout, QLineEdit, QLabel, QHBoxLayout, \
    QDialogButtonBox

from enmapbox.gui.applications import EnMAPBoxApplication
from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer, QgsProcessingParameterNumber, \
    QgsProcessingParameterRasterDestination, QgsProcessingContext, QgsProcessingFeedback
from qgis.gui import QgsFileWidget

VERSION = '0.0.1'
LICENSE = 'GNU GPL-3'
APP_DIR = os.path.dirname(__file__)

APP_NAME = 'My First EnMAPBox App'


class AnacondaExampleEnMAPBoxApp(EnMAPBoxApplication):
    """
    This Class inherits from an EnMAPBoxApplication
    """

    def __init__(self, enmapBox, parent=None):
        super(AnacondaExampleEnMAPBoxApp, self).__init__(enmapBox, parent=parent)

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
        return QIcon(os.path.join(APP_DIR, 'icon.png'))

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

        # this way you can add your QMenu/QAction to another menu entry, e.g. 'Tools'
        # appMenu = self.enmapbox.menu('Tools')

        menu = appMenu.addMenu('Example Anaconda App')
        menu.setIcon(self.icon())

        # add a QAction that starts a process of your application.
        # In this case it will open your GUI.
        a = menu.addAction('Show Anaconda App Parameterization GUI')
        assert isinstance(a, QAction)
        a.triggered.connect(self.startGUI)
        appMenu.addMenu(menu)

        return menu

    def geoAlgorithms(self):
        """
        This function returns the QGIS Processing Framework GeoAlgorithms specified by your application
        :return: [list-of-GeoAlgorithms]
        """

        return [AnacondaCallingGeoAlgorithm()]

    def startGUI(self, *args):
        """
        Opens a GUI
        :param args:
        :return:
        """

        w = AnacondaCallingGUI()
        w.show()


class AnacondaCallingGUI(QWidget):
    """
    A minimal graphical user interface
    """

    def __init__(self, parent=None):
        super(AnacondaCallingGUI, self).__init__(parent)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(os.path.join(APP_DIR, 'icon.png')))
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.mAnacondaRoot = QgsFileWidget(parent=self)
        self.mAnacondaRoot.setFileWidgetButtonVisible(True)
        self.mAnacondaRoot.setStorageMode(QgsFileWidget.GetDirectory)
        self.mAnacondaRoot.fileChanged.connect(self.setAnacondaRoot)

        self.settings = QFrame()
        settingsGrid = QGridLayout()
        self.settings.setLayout(settingsGrid)
        self.mParameter1 = QLineEdit('Hello Anaconda Environment')

        self.mAnacondaScript = QgsFileWidget(parent=self.settings)
        self.mAnacondaScript.setFileWidgetButtonVisible(True)
        self.mAnacondaScript.setStorageMode(QgsFileWidget.GetFile)
        self.mAnacondaScript.setFilePath(os.path.join(APP_DIR, *['conda_code', 'condacodeexamples.py']))

        settingsGrid.addWidget(QLabel('Parameter1'), 0, 0)
        settingsGrid.addWidget(self.mParameter1, 0, 1)
        settingsGrid.addWidget(QLabel('Script'), 1, 0)
        settingsGrid.addWidget(self.mAnacondaScript, 1, 1)

        self.mProcess = None
        ll = QHBoxLayout()
        ll.addWidget(QLabel('Anaconda'))
        ll.addWidget(self.mAnacondaRoot)
        layout.addLayout(ll)
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        bbox.button(QDialogButtonBox.Ok).clicked.connect(self.runAnacondaCode)
        bbox.button(QDialogButtonBox.Close).clicked.connect(self.close)
        layout.addWidget(self.settings)
        layout.addWidget(bbox)

    def runAnacondaCode(self, *args):

        if isinstance(self.mProcess, QProcess):
            self.mProcess.kill()
        self.mProcess = QProcess()
        AI = AnacondaEnvironmentInfo(self.anacondaRoot())
        assert AI.isValid()
        self.mProcess.setWorkingDirectory(AI.rootFolder())
        root = self.anacondaRoot()

        self.mProcess = QProcess()

        s = ""

    def setAnacondaRoot(self, path):
        if self.mAnacondaRoot.filePath() != path:
            self.mAnacondaRoot.setFilePath(path)

        if AnacondaEnvironmentInfo.isAnacondaEnvironment(path):
            # enable other setting
            self.settings.setEnabled(True)
        else:
            # disable other settings
            self.settings.setEnabled(False)

    def anacondaRoot(self):
        return self.mAnacondaRoot.filePath()


class AnacondaEnvironmentInfo(object):
    @staticmethod
    def isAnacondaEnvironment(rootDir):
        """
        Checks is the given rootDir contains a valid Anaconda Environment
        :param rootDir:
        :return: True | False
        """

        if not os.path.isdir(rootDir):
            return False

        requiredSubFolders = ['Scripts', 'Library', 'conda-meta', 'pkgs']
        for subFolder in requiredSubFolders:
            if not os.path.isdir(os.path.join(rootDir, subFolder)):
                return False

        return True

    def __init__(self, rootDir):
        """
        :param rootDir: str, path to root folder of a local Anaconda / Miniconda installation
        """
        assert isinstance(rootDir, str)
        assert os.path.isdir(rootDir)
        self.mRootDir = rootDir
        self.mIsValid = AnacondaEnvironmentInfo.isAnacondaEnvironment(self.mRootDir)

    def pythonExecutable(self):
        if not self.isValid():
            return None
        return os.path.join(self.mRootDir, 'python.exe')

    def scriptFolder(self):
        if not self.isValid():
            return None
        return os.path.join(self.mRootDir, 'Scripts')

    def rootFolder(self):
        self.mRootDir

    def activateScript(self):
        if not self.isValid():
            return None
        return os.path.join(self.scriptFolder(), 'activate.bat')

    def isValid(self):
        """
        Returns True if the given root folder is the root of a valida Anaconda Environment
        :return:
        """
        return self.mIsValid

    def processEnvironment(self):
        if not self.isValid():
            return None

        env = QProcessEnvironment()
        return env


class AnacondaCallingGeoAlgorithm(QgsProcessingAlgorithm):

    def __init__(self):
        super(AnacondaCallingGeoAlgorithm, self).__init__()
        s = ""

    def createInstance(self):
        return AnacondaCallingGeoAlgorithm()

    def name(self):
        return 'exmaplealg'

    def displayName(self):
        return 'Example Algorithm'

    def groupId(self):
        return 'exampleapp'

    def group(self):
        return APP_NAME

    def initAlgorithm(self, configuration=None):
        self.addParameter(QgsProcessingParameterRasterLayer('pathInput', 'The Input Dataset'))
        self.addParameter(
            QgsProcessingParameterNumber('value', 'The value', QgsProcessingParameterNumber.Double, 1, False, 0.00,
                                         999999.99))
        self.addParameter(QgsProcessingParameterRasterDestination('pathOutput', 'The Output Dataset'))

    def processAlgorithm(self, parameters, context, feedback):
        assert isinstance(parameters, dict)
        assert isinstance(context, QgsProcessingContext)
        assert isinstance(feedback, QgsProcessingFeedback)

        outputs = {}
        return outputs


if __name__ == '__main__':

    from enmapbox.testing import initQgisApplication

    # this will initialize the QApplication/QgsApplication which runs in the background
    # see https://qgis.org/api/classQgsApplication.html for details
    qgsApp = initQgisApplication()

    rootAnaconda = r'C:\Users\geo_beja\AppData\Local\Continuum\miniconda3'
    AI = AnacondaEnvironmentInfo(rootAnaconda)

    p = QProcess()

    from enmapbox.gui.mimedata import textFromByteArray

    def readStdOut(p):
        assert isinstance(p, QProcess)

        ba = p.readAllStandardOutput()
        s = str(textFromByteArray(ba)).strip()

        print(s)

    def readStdErr(process):
        assert isinstance(process, QProcess)

        ba = process.readAllStandardError()
        s = str(textFromByteArray(ba)).strip()
        import sys
        print(s, file=sys.stderr)

    pathPythonScript = os.path.join(APP_DIR, *['conda_code', 'condacodeexamples.py'])
    assert os.path.isfile(pathPythonScript)
    startScripts = [
        # 'set path=',
        'set pythonpath=',
        'echo change dir',
        'cd {}'.format(os.path.dirname(AI.activateScript())),
        'call activate.bat ',
        'call python -c "import sys;print(\'\\n\'.join(sys.path))"'
        # 'call python.exe {}'.format(pathPythonScript)

    ]
    pathStartScript = os.path.normpath(os.path.join(APP_DIR, *['conda_code', 'runconda.bat']))

    file = open(pathStartScript, 'w', encoding='UTF-8')
    file.write('\n'.join(startScripts))
    file.flush()
    file.close()

    import subprocess

    r = subprocess.check_output(pathStartScript, shell=True)
    print(r.decode('ascii'))

    p.readyReadStandardError.connect(lambda p=p: readStdErr(p))
    p.readyReadStandardOutput.connect(lambda p=p: readStdOut(p))
    p.started.connect(lambda: print('started'))
    p.finished.connect(lambda: print('finished'))
    p.start(pathStartScript)
    assert p.startDetached(pathStartScript)

    if True:  # test GUI without EnMAP-Box
        w = AnacondaCallingGUI()
        w.setAnacondaRoot(rootAnaconda)
        w.show()

    else:
        from enmapbox.gui.enmapboxgui import EnMAPBox

        EB = EnMAPBox(None)
        EB.run()
        EB.openExampleData(mapWindows=2)
        app = ExampleEnMAPBoxApp(EB)
        EB.addApplication(app)

    # start the GUI thread
    qgsApp.exec_()
