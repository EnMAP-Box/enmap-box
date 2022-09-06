# -*- coding: utf-8 -*-

"""
***************************************************************************
    exampleapp/sandbox.py

    An exemplary sandbox to play around and test how and if things work.
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

"""
This sandbox can be used to run your EnMAP-Box Application without starting a (heavy) QGIS Instance.
"""


def sandboxShowAppInEnMapBox(loadPF=True):
    """
    A minimum example that shows how to load the EnMAP-Box
    :param loadPF: Set on True to initialize the QGIS Processing Framework (takes longer).
    This is required if your app contributes GeoAlgorithms to the EnMAPBoxAlgorithmProvider.
    """
    """Minimum example to the this application"""

    from enmapbox.gui.enmapboxgui import EnMAPBox
    EB = EnMAPBox(None)
    EB.run()
    EB.openExampleData(mapWindows=2)

    # now load your App into the EnMAP-Box
    import os
    appDir = os.path.dirname(__file__)
    EB.addApplication(appDir)


def sandboxShowAppGuiOnly():
    """
    Show & Test the GUI, without any EnMAP-Box / QGIS
    :return:
    """
    from userinterfaces import ExampleGUI
    ui1 = ExampleGUI()
    ui1.show()


if __name__ == '__main__':

    from enmapbox.testing import initQgisApplication

    # this will initialize the QApplication/QgsApplication which runs in the background
    # see https://qgis.org/api/classQgsApplication.html for details
    qgsApp = initQgisApplication()

    if False:
        sandboxShowAppGuiOnly()
    else:
        sandboxShowAppInEnMapBox(True)

    # start the GUI thread
    qgsApp.exec_()
