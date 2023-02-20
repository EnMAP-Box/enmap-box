# -*- coding: utf-8 -*-
#
# Copyright © 2019 / Dr. Stéphane Guillaso
# Licensed under the terms of the 
# (see ../LICENSE.md for details)

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
import time
import hys
import os
import csv

class ui_val:

    def __init__(self, parent=None):
        super(ui_val, self).__init__(parent=parent)
    
    def insert_val(self, dname):
        
        # self.val_soil_prod = []
        self.val_soil_dname = dname
        self.val_csv_fname = None
        self.val_csv_array = []
        self.val_csv_out = None

        self.val_csv_data = hys.CSV_DATA()

        # =========================================================================================
        # CREATE THE TAB: SOIL CALIBRATING
        self.gui.widget_tab_page(title = 'Validate')


        # -----------------------------------------------------------------------------------------
        # GROUP BOX: INPUT
        self.gui.widget_group_box('INPUT')

        # first line
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_label(text='Calibrated soil product[s]', width=170)
        self.gui.widget_list(ID='val_list_calibrated_soil_product')
        self.gui.widget_column(alignment=Qt.AlignTop)
        width = 50
        self.gui.widget_tool_button(text='Add'   , width=width, action=self.val_add_soil)
        self.gui.widget_tool_button(text='Remove', width=width, action=self.val_rem_soil)
        self.gui.widget_tool_button(text='Up',     width=width, action=self.val_up__soil)
        self.gui.widget_tool_button(text='Down',   width=width, action=self.val_dwn_soil)
        self.gui.widget_tool_button(text='Clear',  width=width, action=self.val_clr_soil)
        self.gui.widget_column_close()
        self.gui.widget_row_close()

        # second line
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_label(text='Reference points [CSV]', width=170)
        self.gui.widget_push_button('Load', action=self.val_load_csv, width=50, ID='val_but_csv_load')
        # self.gui.widget_push_button('View')
        self.gui.widget_label(ID='val_lab_csv', text='No data loaded')
        # self.gui.widget_text(ID='val_txt_csv_fname')
        # self.gui.widget_tool_button(text='Import', action=self.val_get_csv)
        # self.gui.widget_tool_button(text='View',   action=self.val_view_csv)
        self.gui.widget_row_close()

        # third line
        # self.gui.widget_row(ID='val_group1', alignment=Qt.AlignLeft)
        # self.gui.widget_label(width=170)
        # valGroupCoordXY = QButtonGroup(self.gui.gui['val_group1'])
        # self.gui.widget_radio_button('Geographical Coordinates', default=True, group=valGroupCoordXY)
        # self.gui.widget_radio_button('Image Coordinates', group=valGroupCoordXY)
        # # self.gui.widget_label(text='# Header line(s):')
        # # self.gui.widget_spinbox(min=0, default=1, ID='val_spinbox_n_header_line')
        # self.gui.widget_row_close()

        # close input boxe
        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: OUTPUT
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box('OUTPUT')
        self.gui.widget_row()
        self.gui.widget_label(text='Validation file [CSV]', width=170)
        self.gui.widget_text(ID='val_text_out_fname')
        self.gui.widget_tool_button(text='...', action=self.val_save_csv)
        self.gui.widget_row_close()
        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: PARAMETER
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box('PARAMETER')
        self.gui.widget_row(ID = 'val_group2', alignment=Qt.AlignLeft)
        self.gui.widget_label(text = 'Average window size')
        valGroupPrms = QButtonGroup(self.gui.gui['val_group2'])
        self.gui.widget_radio_button('1x1', group=valGroupPrms, ID='val_1x1')
        self.gui.widget_radio_button('3x3', group=valGroupPrms, ID='val_3x3', default=True)
        self.gui.widget_radio_button('5x5', group=valGroupPrms, ID='val_5x5')
        self.gui.widget_radio_button('7x7', group=valGroupPrms, ID='val_7x7')
        self.gui.widget_row_close()
        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: RUN
        self.gui.widget_add_stretch()
        self.gui.widget_group_box('PROCESS', layout='H')
        self.gui.widget_push_button('Run...', action=self.val_exe)
        self.gui.widget_progress(height=10)
        # self.gui.widget_push_button('Plot results...')
        self.gui.widget_group_box_close()


        # =========================================================================================
        # CLOSE THE TAB: SOIL MAPPING
        self.gui.widget_tab_page_close()




    ###############################################################################################
    #
    # ADD CALIBRATED SOIL PRODUCT
    #
    ###############################################################################################
    def val_add_soil(self):
        title = self.app_name + " - Select a calibrated soil product"
        dname = self.val_soil_dname
        filenames = hys.pick_file(self, title=title, dname=dname, multiple=True)
        if filenames == []:
            return
        for filename in filenames:
            status, soil = hys.data().open(filename)
            if status is False:
                continue
            if type(soil) != hys.product:
                continue
            self.gui.gui['val_list_calibrated_soil_product'].addItem(filename)
            dname = os.path.dirname(filename)
        self.val_soil_dname = dname




    ###############################################################################################
    #
    # REMOVE SELECTED ITEM
    #
    ###############################################################################################
    def val_rem_soil(self):
        if self.gui.gui['val_list_calibrated_soil_product'].count() == 0:
            return
        curRow = self.gui.gui['val_list_calibrated_soil_product'].currentRow()
        self.gui.gui['val_list_calibrated_soil_product'].takeItem(curRow)




    ###############################################################################################
    #
    # MOVE SELECTED ITEM UP
    #
    ###############################################################################################
    def val_up__soil(self):
        curRow = self.gui.gui['val_list_calibrated_soil_product'].currentRow()
        item = self.gui.gui['val_list_calibrated_soil_product'].takeItem(curRow-1)
        self.gui.gui['val_list_calibrated_soil_product'].insertItem(curRow, item)




    ###############################################################################################
    #
    # MOVE SELECTED ITEM DOWN
    #
    ###############################################################################################
    def val_dwn_soil(self):
        curRow = self.gui.gui['val_list_calibrated_soil_product'].currentRow()
        item = self.gui.gui['val_list_calibrated_soil_product'].takeItem(curRow+1)
        self.gui.gui['val_list_calibrated_soil_product'].insertItem(curRow, item)




    ###############################################################################################
    #
    # CLEAR LIST ITEM
    #
    ###############################################################################################
    def val_clr_soil(self):
        self.gui.gui['val_list_calibrated_soil_product'].clear()




    ###############################################################################################
    #
    # GET CSV FILE
    #
    ###############################################################################################
    def val_load_csv(self):
        dname = self.val_soil_dname
        if self.val_csv_data.fname is not None:
            dname = os.path.dirname(self.val_csv_data.fname)
        self.val_csv = hys.gui.CSV(dname, self, 'val_but_csv_load', 'val_lab_csv', self.val_csv_data)




    ###############################################################################################
    #
    # SAVE CSV OUTPUT FILE
    #
    ###############################################################################################
    def val_save_csv(self):
        title = self.app_name + " - Save csv output file"
        if self.val_csv_out is None:
            dname = self.val_soil_dname
        else:
            dname = os.path.dirname(self.val_csv_out)
        filename = hys.pick_file(self, title=title, dname=dname, filter='*.csv', write=True)
        if filename == "":
            return
        self.val_csv_out = filename
        self.gui.gui['val_text_out_fname'].setText(filename)




    ###############################################################################################
    #
    # VALIDATE DATA
    #
    ###############################################################################################
    def val_exe(self):

        # check if input file(s) are present
        n_item = self.gui.gui['val_list_calibrated_soil_product'].count()
        if n_item == 0:
            hys.display_error(self, 'Select one soil product (at least)')
            return
        
        # check if an input csv file is present
        if self.val_csv_data.rows == []:
            hys.display_error(self, 'Select a csv file')
            return
        
        # check if an output file is present
        if self.val_csv_out is None:
            hys.display_error(self, 'Select a output csv file')
            return

        # check if number of input file are corresponding to the number of reference element to be calculated
        n_cols = self.val_csv_data.n_cols
        if n_item != (n_cols - 3):
            hys.display_error(self, 'Number of files ('+str(n_item)+') does not fit with number of element ('+str(n_cols-3)+').')
            return

        # get array with filename
        prods = []
        for k in range(n_item):
            fname = self.gui.gui['val_list_calibrated_soil_product'].item(k).text()
            st, prod = hys.data().open(fname)
            prods.append(prod)
        if self.val_csv_data.coordinates == 1:
            map_info = prods[0].meta['map info']
        else:
            map_info = None
        
        # get the image dimensions
        dim = [prods[0].samples, prods[0].lines]

        # get win size
        if   self.gui.gui['val_1x1'].isChecked(): wsize = 1
        elif self.gui.gui['val_3x3'].isChecked(): wsize = 3
        elif self.gui.gui['val_5x5'].isChecked(): wsize = 5
        else:                                     wsize = 7

        t1 = time.time()
        ofile = open(self.val_csv_out, "w")

        # we suppose that we have an header
        first_line = [self.val_csv_data.hrows[0]]
        for k in range(n_cols-3):
            first_line.append(self.val_csv_data.hrows[k+3])
            first_line.append('Estimated ' + self.val_csv_data.hrows[k+3])
        s = ", "
        first_line = s.join(first_line)
        ofile.write(first_line+"\n")
        n_rows = np.int64(self.val_csv_data.n_rows)
        self.gui.gui['cal_prog_bar'].setMinimum(0)
        self.gui.gui['cal_prog_bar'].setMaximum(n_rows)
        for k in range(n_rows):
            self.gui.gui['cal_prog_bar'].setValue(k+1)
            xpos = np.float32(self.val_csv_data.rows[k][1])
            ypos = np.float32(self.val_csv_data.rows[k][2])
            status, box = hys.coord2pts(xpos, ypos, map_info, dim, wsize)
            if status is False: continue
            line = [self.val_csv_data.rows[k][0]]
            for n in range(n_item):
                im = np.mean(prods[n].read(BLOCK=box))
                line.append(self.val_csv_data.rows[k][n+3])
                line.append(str(im))
            s = ", "
            line = s.join(line) + "\n"
            ofile.write(line)            
        
        ofile.close()
        
        msg = "Processing complele in %8.2f seconds"%(time.time() - t1)
        hys.display_information(self, msg)
        self.gui.gui['cal_prog_bar'].setValue(0)
