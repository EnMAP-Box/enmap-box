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

Changelog
EnGeoMAP Version 3.1
Date: April 2022
Author: Helge L. C. Daempfling
Email: hdaemp@gfz-potsdam.de

Several modifications were realized and new functions and features have
been added to the UI, while others were removed.
- The UI now uses multithreading with a Qthreadpool,
and QRunnable Worker functions in order to prevent freezing of the UI
once processing has started. functions to display a busy and ready
status in the GUI have been added.
- EnGeoMAP's algorithms are now called over the Algo_multi function
and the connected Worker class and threadpool.
- The previous version ready and busy display over images has been removed.
- The Lab image and Lab Library tick boxes were removed as they were just
non-working placeholders for a future development.
"""

import os

from qgis.PyQt.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, Qt
from qgis.PyQt.QtWidgets import QFileDialog, QDialog, QMessageBox

from engeomap import APP_DIR
from enmapbox.gui.utils import loadUIFormClass
from enmapbox.qgispluginsupport.qps.utils import loadUi

""""
Use the QtDesigner to design a GUI and save it as *.ui file
The example.ui can get compiled and loaded at runtime.
"""""

pathUi = os.path.join(APP_DIR, 'engeomap_base.ui')
pathUi2 = os.path.join(APP_DIR, 'busyqt4.ui')
p = dict()


def checkstatus(objectus):
    if objectus.isChecked():
        nd = 1
    else:
        nd = 0
    return nd


def button_paths(objectus):
    path = objectus


def selectFile(objectt):
    feil = QFileDialog.getOpenFileName()
    objectt.setText(feil[0])
    objectt.show()
    return None


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data
    '''
    started = pyqtSignal()
    finished = pyqtSignal()

# worker class
class Worker(QRunnable):
    '''
        Worker thread
    '''

    signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        # emit started signal:
        self.signals.started.emit()
        # Pass collected parameters from UI elements to algorithms and start calculations
        params = p
        from engeomap.algorithms import engeomapp_headless
        from engeomap.algorithms import mapper_fullrange

        # Calculation:
        engeomapp_headless(params)
        mapper_fullrange(params)

        # emit finished signal:
        self.signals.finished.emit()



class EnGeoMAPGUI(QDialog):
    """Constructor."""
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        loadUi(pathUi, self)
        self.enmap_data.clicked.connect(self.selectFile1)
        self.choose_lib.clicked.connect(self.selectFile2)
        self.choose_csv.clicked.connect(self.selectFile3)
        self.threadpool = QThreadPool()
        self.worker = Worker()
        self.buttonBox.accepted.connect(self.Algo_Multi) # Button Box
        self.buttonBox.rejected.connect(self.close)
        p = self.frame_5.palette()
        p.setColor(self.frame_5.backgroundRole(), Qt.green)
        self.frame_5.setPalette(p)
        self.frame_5.update()
        self.frame_5.show()

    def Algo_Multi(self):
        QMessageBox.about(self, "Notice",
                          "EnGeoMAP will now classify your data. " +
                          "This might take a few hours depending on the size of your data. " +
                          "\n" +
                          "\nPress OK to proceed.")
        # Call collection of parameter from UI input
        self.collectParameters()
        # Start the worker process (start calculations via Worker class run function)
        self.threadpool.start(self.worker)
        # Set Status to busy
        self.worker.signals.started.connect(
            lambda: self.label_5.setText("Status: Busy processing data...")
        )
        self.worker.signals.started.connect(self.Im_Busy)
        # Disable buttonBox
        self.buttonBox.setEnabled(False)
        self.update()
        self.show()
        # Display Ready Message
        self.worker.signals.finished.connect(self.Im_Ready)
        self.update()
        self.show()

    def Im_Ready(self):
        # Enable buttonBox after worker thread finished
        self.buttonBox.setEnabled(True)
        # Message to user that processing has finished.
        QMessageBox.about(self, "Finished Processing", "EnGeoMAP has finished processing your data. " +
                          "The data Products are now available in your data source folder.")
        # Reset Status text to ready
        self.label_5.setText("Status: Ready to process Data")
        # Reset Status indicator (label_5) color to green
        p = self.frame_5.palette()
        p.setColor(self.frame_5.backgroundRole(), Qt.green)
        self.frame_5.setPalette(p)
        self.frame_5.update()
        self.frame_5.show()

    def Im_Busy(self):
        p = self.frame_5.palette()
        p.setColor(self.frame_5.backgroundRole(), Qt.red)
        self.frame_5.setPalette(p)
        self.frame_5.update()
        self.frame_5.show()

    def collectParameters(self):
        """
        Collect the parameterization from the UI elements.
        :return: dictionary (dict) with parameters
        """
        global p
        L = []
        p['vnirt'] = self.vnir_thresh.toPlainText()
        p['swirt'] = self.swir_thresh.toPlainText()
        p['fit_thresh'] = self.fit_thresh.toPlainText()
        p['mixminerals'] = self.ixminerals.toPlainText()
        # p['laboratory'] = checkstatus(self.lab_image)
        # p['liblab'] = checkstatus(self.lab_lib)
        p['image'] = self.input_image.text()
        p['library'] = self.speclib.text()
        p['farbe'] = self.colormap.text()
        return p

    def selectFile1(self):
        self.input_image.setText(QFileDialog.getOpenFileName()[0])

    def selectFile2(self):
        self.speclib.setText(QFileDialog.getOpenFileName()[0])

    def selectFile3(self):
        self.colormap.setText(QFileDialog.getOpenFileName()[0])
