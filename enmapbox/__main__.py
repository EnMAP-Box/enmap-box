# -*- coding: utf-8 -*-

"""
***************************************************************************
    __main__
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
**************************************************************************
"""
import argparse
import pathlib
import site
import sys

from enmapbox import initAll
from qgis.PyQt.QtGui import QGuiApplication
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsApplication

site.addsitedir(pathlib.Path(__file__).parents[1])
from enmapbox.testing import start_app
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.resources import findQGISResourceFiles

qApp: QgsApplication = None


def exitAll(*args):
    print('## Close all windows')
    QApplication.closeAllWindows()
    QApplication.processEvents()
    print('## Quit QgsApplication')
    QgsApplication.quit()
    print('## QgsApplication down')
    qApp = None
    sys.exit(0)


def run(
        sources: list = None,
        initProcessing=False,
        load_core_apps=False, load_other_apps=False,
        debug: bool = False
):
    """
    Starts the EnMAP-Box GUI.
    """
    global qApp
    qAppExists = isinstance(qApp, QgsApplication)
    if not qAppExists:
        print('## Create a QgsApplication...')
        qApp = start_app(resources=findQGISResourceFiles())
        QGuiApplication.instance().lastWindowClosed.connect(qApp.quit)
        print('## QgsApplication created')
    else:
        print('## QgsApplication exists')

    initAll()

    enmapBox = EnMAPBox(load_core_apps=load_core_apps, load_other_apps=load_other_apps)
    enmapBox.run()
    print('## EnMAP-Box started')
    if True and sources is not None:
        for source in enmapBox.addSources(sourceList=sources):
            from enmapbox.gui.datasources.datasources import SpatialDataSource
            if isinstance(source, SpatialDataSource):
                try:
                    # add as map
                    lyr = source.asMapLAyer()
                    dock = enmapBox.createDock('MAP')
                    dock.addLayers([lyr])
                except Exception as ex:
                    pass

    if not qAppExists:
        print('Execute QgsApplication')
        enmapBox.sigClosed.connect(exitAll)
        exit_code = qApp.exec_()
        return exit_code
    else:
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the EnMAP-Box')
    parser.add_argument('-d', '--debug', required=False, help='Debug mode with more outputs', action='store_true')
    # parser.add_argument('-x', '--no_exec', required=False, help='Close EnMAP-Box if QApplication is not existent',
    #                    action='store_true')
    args = parser.parse_args()

    run(debug=args.debug, initProcessing=True, load_core_apps=True, load_other_apps=True)
    s = ""
