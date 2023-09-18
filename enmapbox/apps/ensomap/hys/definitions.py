# -*- coding: utf-8 -*-
#
# Copyright © 2018 Stephane Guillaso
# Licensed under the terms of 
# (see ../LICENSE.md for details)
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import time
import numpy as np

def display_error(parent, msg):
    QMessageBox.critical(
        parent,
        "HYSOMA - Error",
        msg,
        QMessageBox.Ok,
        QMessageBox.Ok
    )





def display_information(parent, msg):
    QMessageBox.information(
        parent,
        "HYSOMA - Information",
        msg,
        QMessageBox.Ok,
        QMessageBox.Ok
    )





def pick_file(parent, dname=None, title=None, directory=None, filter=None, multiple=False, write=False):
    if dname is None: dname = os.path.expanduse('~')
    if directory is None:
        if filter is None: filter="All Files (*)"
        if write is True:
            fname, _ = QFileDialog.getSaveFileName(parent, title, dname, filter)
            return fname
        if multiple is True:
            fname, _ = QFileDialog.getOpenFileNames(parent, title, dname, filter)
            return fname
        fname, _ = QFileDialog.getOpenFileName(parent, title, dname, filter)
        return fname
    return QFileDialog.getExistingDirectory(parent, title, dname)



class displayText(QWidget):
    def __init__(self, title, msg, parent=None):
        super(displayText, self).__init__(parent=parent)
        self.setWindowTitle("Display: " + title)
        self.mainGrid = QVBoxLayout()
        self.setLayout(self.mainGrid)
        self.setGeometry(0, 0, 700, 400)
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        Line1Layout = QHBoxLayout()
        Line1Button = QPushButton('Close')
        Line1Button.clicked.connect(self.cancel)
        Line1Layout.addWidget(Line1Button)
        Line1Layout.addStretch()
        self.mainGrid.insertLayout(-1, Line1Layout)
        Line2Layout = QVBoxLayout()
        Line2Txt = QTextEdit()
        Line2Txt.setPlainText(msg)
        Line2Txt.setReadOnly(True)
        font = QFont()
        font.setFamily('Monospace')
        Line2Txt.setFont(font)
        Line2Layout.addWidget(Line2Txt)
        self.mainGrid.insertLayout(-1, Line2Layout)
        self.show()
        self.center()
    def cancel(self):
        self.close()
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    


def coord2pts(xpos, ypos, map_info, dim, wsize, option=False):
    if option:
        x = xpos - 1
        y = ypos - 1
    else:
        x0    = np.float32(map_info[1]) - 1
        y0    = np.float32(map_info[2]) - 1
        xref  = np.float32(map_info[3])
        yref  = np.float32(map_info[4])
        xstep = np.float32(map_info[5])
        ystep = np.float32(map_info[6])
        x = np.abs(xpos - xref) / xstep + x0
        y = np.abs(ypos - yref) / ystep + y0
    
    xmin = np.int64(x - wsize//2)
    if xmin < 0: xmin = 0
    xmax = np.int64(x + wsize//2)
    if xmax > (dim[0]-1): xmax = dim[0]-1
    ymin = np.int64(y - wsize//2)
    if ymin < 0: ymin = 0
    ymax = np.int64(y + wsize//2)
    if ymax > (dim[1] - 1): ymax = dim[1]-1

    if xmin > xmax: return False, None
    if ymin > ymax: return False, None

    return True, np.asarray([xmin, xmax, ymin, ymax], dtype=np.int64)






class report:
    def __init__(self, rname):
        exe_time = time.strftime("%Y%m%d-%H%M%S")
        lname = rname + "_" + exe_time + ".log"
        txt  = "**********************************************************\n"
        txt += "**********************************************************\n"
        txt += "                 H Y S O M A   R E P O R T                \n"
        txt += "**********************************************************\n"
        txt += "**********************************************************\n"
        txt += "\n\n"
        txt += "This file has been generated at: " + exe_time + "\n\n"
        self.file = open(lname, 'w')
        self.file.write(txt)
        #define soil product
        self.soil_products = {}

    def add_information(self, msg):
        self.file.write(msg+"\n\n")
    
    def add_product(self, id, name):
        prod = {}
        prod['name'] = name
        prod['status'] = ''
        prod['lbands'] = ''
        prod['ubands'] = ''
        self.soil_products[id] = prod
    
    def set_product_status(self, id, msg):
        self.soil_products[id]['status'] = msg
    
    def set_product_lit_bands(self, id, lbands):
        msg = "Literature bands:        " + " ".join(str(x) for x in lbands)
        self.soil_products[id]['lbands'] = msg
    
    def set_product_sel_bands(self, id, ubands):
        if ubands[0] < 100: ubands *= 1000.
        msg = "Hysoma selected bands:   "
        msg += " ".join(str(int(x)) for x in ubands)
        self.soil_products[id]['ubands'] = msg
    
    def write_product(self):
        for key, prod in self.soil_products.items():
            self.file.write("------------------------------------\n")
            self.file.write("\n")
            self.file.write(prod['name'] + "\n")
            if prod['lbands'] != '':
                self.file.write("\n" + prod['lbands'] + "\n")
            if prod['ubands'] != '':
                self.file.write(prod['ubands'] + "\n")
            self.file.write(prod['status'] + "\n\n")
    
    def done(self):
        self.file.close()
