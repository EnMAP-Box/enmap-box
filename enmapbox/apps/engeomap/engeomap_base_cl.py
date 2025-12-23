# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/christian/.qgis2/python/plugins/enmapboxplugin/enmapbox/apps/engeomap/engeomap_base.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!
"""
***************************************************************************
    exampleapp/enmapboxintegration.py

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

from PyQt5 import QtCore, QtWidgets

class Ui_dialog(object):
    def setupUi(self, dialog):
        dialog.setObjectName("dialog")
        dialog.resize(1146, 342)
        dialog.setMouseTracking(False)
        self.frame = QtWidgets.QFrame(dialog)
        self.frame.setGeometry(QtCore.QRect(0, 10, 1151, 131))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.enmap_data = QtWidgets.QPushButton(self.frame)
        self.enmap_data.setGeometry(QtCore.QRect(0, 10, 161, 31))
        self.enmap_data.setObjectName("enmap_data")
        self.choose_lib = QtWidgets.QPushButton(self.frame)
        self.choose_lib.setGeometry(QtCore.QRect(0, 50, 161, 31))
        self.choose_lib.setObjectName("choose_lib")
        self.choose_csv = QtWidgets.QPushButton(self.frame)
        self.choose_csv.setGeometry(QtCore.QRect(0, 90, 161, 31))
        self.choose_csv.setObjectName("choose_csv")
        self.input_image = QtWidgets.QLineEdit(self.frame)
        self.input_image.setGeometry(QtCore.QRect(170, 10, 971, 31))
        self.input_image.setObjectName("input_image")
        self.speclib = QtWidgets.QLineEdit(self.frame)
        self.speclib.setGeometry(QtCore.QRect(170, 50, 971, 31))
        self.speclib.setObjectName("speclib")
        self.colormap = QtWidgets.QLineEdit(self.frame)
        self.colormap.setGeometry(QtCore.QRect(170, 90, 971, 31))
        self.colormap.setObjectName("colormap")
        self.frame_2 = QtWidgets.QFrame(dialog)
        self.frame_2.setGeometry(QtCore.QRect(0, 150, 421, 181))
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.vnir_thresh = QtWidgets.QTextEdit(self.frame_2)
        self.vnir_thresh.setGeometry(QtCore.QRect(340, 10, 71, 31))
        self.vnir_thresh.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.vnir_thresh.setOverwriteMode(False)
        self.vnir_thresh.setObjectName("vnir_thresh")
        self.label = QtWidgets.QLabel(self.frame_2)
        self.label.setGeometry(QtCore.QRect(10, 10, 301, 31))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.frame_2)
        self.label_2.setGeometry(QtCore.QRect(10, 60, 331, 31))
        self.label_2.setObjectName("label_2")
        self.swir_thresh = QtWidgets.QTextEdit(self.frame_2)
        self.swir_thresh.setGeometry(QtCore.QRect(340, 60, 71, 31))
        self.swir_thresh.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.swir_thresh.setOverwriteMode(False)
        self.swir_thresh.setObjectName("swir_thresh")
        self.label_3 = QtWidgets.QLabel(self.frame_2)
        self.label_3.setGeometry(QtCore.QRect(10, 100, 301, 31))
        self.label_3.setObjectName("label_3")
        self.fit_thresh = QtWidgets.QTextEdit(self.frame_2)
        self.fit_thresh.setGeometry(QtCore.QRect(340, 100, 71, 31))
        self.fit_thresh.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.fit_thresh.setOverwriteMode(False)
        self.fit_thresh.setObjectName("fit_thresh")
        self.label_4 = QtWidgets.QLabel(self.frame_2)
        self.label_4.setGeometry(QtCore.QRect(10, 140, 301, 31))
        self.label_4.setObjectName("label_4")
        self.ixminerals = QtWidgets.QTextEdit(self.frame_2)
        self.ixminerals.setGeometry(QtCore.QRect(340, 140, 71, 31))
        self.ixminerals.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.ixminerals.setOverwriteMode(False)
        self.ixminerals.setObjectName("ixminerals")
        self.frame_3 = QtWidgets.QFrame(dialog)
        self.frame_3.setGeometry(QtCore.QRect(420, 150, 131, 81))
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.lab_lib = QtWidgets.QCheckBox(self.frame_3)
        self.lab_lib.setGeometry(QtCore.QRect(20, 40, 101, 25))
        self.lab_lib.setAutoExclusive(False)
        self.lab_lib.setObjectName("lab_lib")
        self.lab_image = QtWidgets.QCheckBox(self.frame_3)
        self.lab_image.setGeometry(QtCore.QRect(20, 10, 93, 25))
        self.lab_image.setChecked(False)
        self.lab_image.setAutoRepeat(False)
        self.lab_image.setAutoExclusive(False)
        self.lab_image.setObjectName("lab_image")
        self.frame_4 = QtWidgets.QFrame(dialog)
        self.frame_4.setGeometry(QtCore.QRect(420, 250, 131, 71))
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")
        self.hyperion_psf = QtWidgets.QCheckBox(self.frame_4)
        self.hyperion_psf.setGeometry(QtCore.QRect(10, 40, 111, 25))
        self.hyperion_psf.setAutoExclusive(True)
        self.hyperion_psf.setObjectName("hyperion_psf")
        self.buttonGroup = QtWidgets.QButtonGroup(dialog)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.hyperion_psf)
        self.enmap_psf = QtWidgets.QCheckBox(self.frame_4)
        self.enmap_psf.setGeometry(QtCore.QRect(10, 10, 111, 25))
        self.enmap_psf.setChecked(True)
        self.enmap_psf.setAutoExclusive(True)
        self.enmap_psf.setObjectName("enmap_psf")
        self.buttonGroup.addButton(self.enmap_psf)
        self.buttonBox = QtWidgets.QDialogButtonBox(dialog)
        self.buttonBox.setGeometry(QtCore.QRect(560, 290, 166, 28))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.Ready = QtWidgets.QGraphicsView(dialog)
        self.Ready.setGeometry(QtCore.QRect(950, 150, 181, 161))
        self.Ready.setObjectName("Ready")
	    # self.Ready.type
        self.retranslateUi(dialog)
        QtCore.QMetaObject.connectSlotsByName(dialog)

    def retranslateUi(self, dialog):
        _translate = QtCore.QCoreApplication.translate
        dialog.setWindowTitle(_translate("dialog", "EnGeoMAP BASE"))
        self.enmap_data.setText(_translate("dialog", "EnMAP Data"))
        self.choose_lib.setText(_translate("dialog", "Spectral Library"))
        self.choose_csv.setText(_translate("dialog", "Legend Colors"))
        self.vnir_thresh.setHtml(_translate("dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">0.02</p></body></html>"))
        self.label.setText(_translate("dialog", "VNIR Reflactance Threshold up to 1000 nm"))
        self.label_2.setText(_translate("dialog", "SWIR Reflactance Threshold from 1000-2500 nm"))
        self.swir_thresh.setHtml(_translate("dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">0.03</p></body></html>"))
        self.label_3.setText(_translate("dialog", "Minimum Fit Threshold Weighted Fitting"))
        self.fit_thresh.setHtml(_translate("dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">0.5</p></body></html>"))
        self.label_4.setText(_translate("dialog", "Maximum Number of Endmembers in Unmixing"))
        self.ixminerals.setHtml(_translate("dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">9</p></body></html>"))
        self.lab_lib.setText(_translate("dialog", "Lab Library"))
        self.lab_image.setText(_translate("dialog", "Lab Image"))
        self.hyperion_psf.setText(_translate("dialog", "Hyperion PSF"))
        self.enmap_psf.setText(_translate("dialog", "EnMAP PSF"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()
    ui = Ui_dialog()
    ui.setupUi(dialog)
    dialog.show()
    sys.exit(app.exec_())

