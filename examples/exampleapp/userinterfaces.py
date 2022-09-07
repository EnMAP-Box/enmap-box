# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/userinterfaces.py

    Some exemplary (graphical) user interfaces, making use of the Qt framework.
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
from enmapbox.qgispluginsupport.qps.utils import loadUi
from examples.exampleapp import APP_DIR
from qgis.PyQt.QtWidgets import QDialog

"""
Use the QtDesigner to open the example.ui file.
The example.ui can get compiled and loaded at runtime.
"""

pathUi = os.path.join(APP_DIR, 'example.ui')


class ExampleGUI(QDialog):
    """Constructor."""

    def __init__(self, parent=None):
        super(ExampleGUI, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        # Important!!!!!!!!! this will initiate all the QWidgets etc. specified in the *.ui file
        self.setupUi(self)
        loadUi(pathUi, self)
        # Connect widgets, add logic that can not be expressed in the QDesginer and needs to be "hard-coded"
        self.buttonBox.accepted.connect(self.startAlgorithm)
        self.buttonBox.rejected.connect(self.close)

    def collectParameters(self):
        """
        Collects parameters from the UI elements.
        :return: dictionary (dict) with parameters
        """
        p = dict()
        p['parameter1'] = self.comboBoxParameter1.currentText()
        p['parameter2'] = None
        return p

    def startAlgorithm(self):
        params = self.collectParameters()
        from algorithms import dummyAlgorithm
        dummyAlgorithm(**params)
