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

class ui_cal:

    def __init__(self, parent=None):
        super(ui_cal, self).__init__(parent=parent)
    
    def insert_cal(self, dname):
        
        # calibration input product
        self.cal_prod  = None

        # calibration output directory pathname
        self.cal_dname = dname

        # calibration from CSV file
        self.cal_csv_data = hys.CSV_DATA()

        # calibration SSL product
        self.cal_ssl_prod_fname = None
        self.cal_ssl_refs_fname = None


        # =========================================================================================
        # CREATE THE TAB: SOIL CALIBRATING
        self.gui.widget_tab_page(title = 'Calibrate')


        # -----------------------------------------------------------------------------------------
        # GROUP BOX: INPUT
        self.gui.widget_group_box('INPUT')
        
        # first line
        self.gui.widget_row()
        self.gui.widget_label(text="Soil Product File:", width=170)
        self.gui.widget_text(ID='cal_txt_soil_product_file_pathname')
        self.gui.widget_tool_button(text='...', action=self.cal_getdata)
        self.gui.widget_row_close()

        # second line
        self.gui.widget_row()
        self.gui.widget_label(width=170)
        self.gui.widget_label(width=700, ID='cal_lab_soil_product_info')
        self.gui.widget_row_close()

        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: OUTPUT
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box('OUTPUT')
        
        self.gui.widget_row()
        self.gui.widget_label(text='Cal. Product Directory', width=170)
        self.gui.widget_text(text=self.cal_dname, ID='cal_txt_dname')
        self.gui.widget_tool_button(text='...', action=self.cal_getdir)
        self.gui.widget_row_close()

        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: PARAMETERS
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box('PARAMETERS')
        self.gui.widget_row()
        self.gui.widget_label(text='Gain:')
        self.gui.widget_text(ID='cal_txt_gain', edit=True)
        self.gui.widget_label(text='Offset:')
        self.gui.widget_text(ID='cal_txt_offset', edit=True)
        self.gui.widget_tool_button(text='Reset', action=self.cal_clear_gain_offset)
        self.gui.widget_row_close()
        
        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: OPTIONS
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box('OPTIONS')

        self.gui.widget_tab()

        self.gui.widget_tab_page('Estimated from image data')
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_label(text='Reference points [CSV]')
        self.gui.widget_push_button('Load', width=50, ID='cal_but_csv_load', action=self.cal_load_csv)
        self.gui.widget_label(ID='cal_lab_csv', text='No data loaded')
        self.gui.widget_row_close()
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_push_button('Estimate...', action=self.cal_csv_estimate)
        self.gui.widget_row_close()
        self.gui.widget_tab_page_close()

        self.gui.widget_tab_page('Estimated from SSL')
        self.gui.widget_row()
        self.gui.widget_label(text='SSL Product [ENVI]', width=170)
        self.gui.widget_text(ID='cal_txt_ssl_prod')
        self.gui.widget_tool_button(text='...', action=self.cal_get_ssl_prod)
        self.gui.widget_row_close()
        self.gui.widget_row()
        self.gui.widget_label(text='SSL Parameters [ASCII]', width=170)
        self.gui.widget_text(ID='cal_txt_ssl_prm')
        self.gui.widget_tool_button(text='...', action=self.cal_get_ssl_refs)
        self.gui.widget_row_close()
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_push_button('Estimate...', action=self.cal_ssl_estimate)
        self.gui.widget_row_close()
        self.gui.widget_tab_page_close()

        self.gui.widget_tab_close()

        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: RUN
        self.gui.widget_add_stretch()
        self.gui.widget_group_box('PROCESS', layout='H')
        self.gui.widget_push_button('Run...', action=self.cal_exe)
        self.gui.widget_progress(height=10, ID='cal_prog_bar')
        self.gui.widget_group_box_close()



        # =========================================================================================
        # CLOSE THE TAB: SOIL MAPPING
        self.gui.widget_tab_page_close()




    ###############################################################################################
    #
    # GET SOIL PRODUCT DATA PATHNAME
    #
    ###############################################################################################
    def cal_getdata(self):
        title = self.app_name + " - Select a soil product file pathname"
        if self.cal_prod is not None:
            dname = os.path.dirname(self.cal_prod.fname)
        else:
            dname = self.map_dname
        while True:
            filename = hys.pick_file(self, dname = dname, title=title)
            if filename == "":
                return
            status, soil = hys.data().open(filename)
            if status is False:
                hys.display_error(self, soil)
                dname = os.path.dirname(filename)
            elif type(soil) != hys.product:
                msg = os.path.basename(filename) + "\nis not a valid soil product!"
                hys.display_error(self, msg)
                dname = os.path.dirname(filename)
            else:
                break
        self.gui.gui['cal_txt_soil_product_file_pathname'].setText(os.path.basename(filename))
        self.cal_prod = soil
        self.gui.gui['cal_lab_soil_product_info'].setText(self.cal_prod.get_info())




    ###############################################################################################
    #
    # GET CALIBRATED SOIL PRODUCT DIRECTORY
    #
    ###############################################################################################
    def cal_getdir(self):
        title = self.app_name + ' - Select a directory to store calibrated product(s)'
        dname = self.cal_dname
        dname = hys.pick_file(self, title=title, dname=dname, directory=True)
        if dname == "":
            return
        if not os.access(dname, os.W_OK):
            msg = dname + "\nis not writable!"
            hys.display_error(self, msg)
            return
        self.cal_dname = dname
        self.gui.gui['cal_txt_dname'].setText(self.cal_dname)




    ###############################################################################################
    #
    # CLEAR GAIN/OFFSET FIELDS
    #
    ###############################################################################################
    def cal_clear_gain_offset(self):
        self.gui.gui['cal_txt_gain'].setText("")
        self.gui.gui['cal_txt_offset'].setText("")




    ###############################################################################################
    #
    # APPLY CALIBRATION MODEL TO SOIL FEATURE
    #
    ###############################################################################################
    def cal_exe(self):
        
        # check if a soil product has been selected
        if self.cal_prod is None:
            hys.display_error(self, 'Select a soil product first!')
            return
        
        # check if gain and offset has been set
        gain = self.gui.gui['cal_txt_gain'].text()
        offset = self.gui.gui['cal_txt_offset'].text()
        if gain.replace('.', '', 1).isdigit() is False:
            hys.display_error(self, 'Gain is not valid!')
            return
        if offset.replace('-','', 1).replace('.','',1).isdigit() is False:
            hys.display_error(self, 'Offset is not valid!')
            return
        gain = np.float32(gain)
        offset = np.float32(offset)
        if gain == 0:
            hys.display_error(self, 'Gain is zero!')
            return
        
        # setup data tiling
        self.cal_prod.tile_data()

        # setup output product
        pname = self.cal_dname + os.path.sep + os.path.basename((os.path.splitext(self.cal_prod.fname))[0]) + '_cal.dat'
        oprod = hys.product(fname=pname, src=self.cal_prod, tile=True)

        # initialize loop
        t1 = time.time()
        self.gui.gui['cal_prog_bar'].setMinimum(0)
        self.gui.gui['cal_prog_bar'].setMaximum(self.cal_prod.bn)
        for k in range(self.cal_prod.bn):
            self.gui.gui['cal_prog_bar'].setValue(k+1)
            im = self.cal_prod.read(tile=k)
            im = im * gain + offset
            oprod.write(np.asarray(im), tile=k)
        
        # return
        msg = "Processing complele in %8.2f seconds"%(time.time() - t1)
        hys.display_information(self, msg)
        self.gui.gui['cal_prog_bar'].setValue(0)




    ###############################################################################################
    #
    # LOAD CSV FILE
    #
    ###############################################################################################
    def cal_load_csv(self):
        dname = self.cal_dname
        if self.cal_csv_data.fname is not None:
            dname = os.path.dirname(self.cal_csv_data.fname)
        self.cal_csv = hys.gui.CSV(dname, self, 'cal_but_csv_load', 'cal_lab_csv', self.cal_csv_data)




    ###############################################################################################
    #
    # GET SSL PRODUCT FILE PATHNAME
    #
    ###############################################################################################
    def cal_csv_estimate(self):
        
        # check if a soil product has been selected
        if self.cal_prod is None:
            hys.display_error(self, 'Select a soil product first!')
            return
        
        # check if an input csv file is present
        if self.cal_csv_data.rows == []:
            hys.display_error(self, 'Select a csv file')
            return
        
        # check the number of columns of the csv file, should at least 4
        # only the fourth column will be used, should corresponds to the 
        # desired parameter
        n_cols = self.cal_csv_data.n_cols
        if n_cols < 4:
            hys.display_error(self, 'At least 4 columns for the csv file')
            return
        
        # get map info
        if self.cal_csv_data.coordinates == 1:
            map_info = self.cal_prod.meta['map info']
        else:
            map_info = None
        
        # get the dimensions of the image
        dim = [self.cal_prod.samples, self.cal_prod.lines]

        # loop to get the model
        n_rows = self.cal_csv_data.n_rows
        data = [] # np.zeros((n_rows), dtype=np.float32)
        model = [] # np.zeros((n_rows), dtype=np.float32)
        for k in range(n_rows):
            xpos = np.float32(self.cal_csv_data.rows[k][1])
            ypos = np.float32(self.cal_csv_data.rows[k][2])
            status, box = hys.coord2pts(xpos, ypos, map_info, dim, 1)
            if status is False: continue
            im = np.float32(self.cal_prod.read(BLOCK=box))
            if np.isnan(im): continue
            data.append(np.reshape(im, 1)[0])
            model.append(self.cal_csv_data.rows[k][3])
        self.plot_scatter = hys.gui.CAL_EST(self, np.asarray(data), np.asarray(model, dtype=np.float32))





    ###############################################################################################
    #
    # GET SSL PRODUCT FILE PATHNAME
    #
    ###############################################################################################
    def cal_get_ssl_prod(self):
        title = self.app_name + ' - Select a spectral library product file pathname'
        if self.cal_ssl_prod_fname is not None:
            dname = os.path.dirname(self.cal_ssl_prod_fname)
        elif self.cal_ssl_refs_fname is not None:
            dname = os.path.dirname(self.cal_ssl_refs_fname)
        else:
            dname = self.cal_dname
        fname = hys.pick_file(self, title=title, dname=dname)
        if fname == "":
            return
        self.cal_ssl_prod_fname = fname
        self.gui.gui['cal_txt_ssl_prod'].setText(os.path.basename(fname))




    ###############################################################################################
    #
    # GET SSL REFERENCES FILE PATHNAME
    #
    ###############################################################################################
    def cal_get_ssl_refs(self):
        title = self.app_name + ' - Select a spectral library references file pathname'
        if self.cal_ssl_refs_fname is not None:
            dname = os.path.dirname(self.cal_ssl_refs_fname)
        elif self.cal_ssl_prod_fname is not None:
            dname = os.path.dirname(self.cal_ssl_prod_fname)
        else:
            dname = self.cal_dname
        fname = hys.pick_file(self, title=title, dname=dname)
        if fname == "":
            return
        self.cal_ssl_refs_fname = fname
        self.gui.gui['cal_txt_ssl_prm'].setText(os.path.basename(fname))




    ###############################################################################################
    #
    # ESTIMATE GAIN/OFFSET FROM SSL
    #
    ###############################################################################################
    def cal_ssl_estimate(self):
        if self.cal_ssl_prod_fname is None:
            hys.display_error(self, 'Select a SSL product file')
            return
        if self.cal_ssl_refs_fname is None:
            hys.display_error(self, 'Select a SSL references file')
            return
        status, soil = hys.data().open(self.cal_ssl_prod_fname)
        if status is False:
            hys.display_error(self, soil)
            return
        elif type(soil) != hys.product:
            msg  = os.path.basename(self.cal_ssl_prod_fname)
            msg += "\nis not a valid soil product!"
            hys.display_error(self, msg)
            return
        lines = [line.rstrip('\n') for line in open(self.cal_ssl_refs_fname)]
        model = np.asarray(lines, dtype=np.float32)
        data = np.reshape(soil.read(), (soil.lines))
        self.plot_scatter = hys.gui.CAL_EST(self, data, model)

    
