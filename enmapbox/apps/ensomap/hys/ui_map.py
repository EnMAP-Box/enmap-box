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

import hys.feat_specan_adc1   as adc1
import hys.feat_specan_clay1  as adclay1
import hys.feat_specan_fe1    as adfe1
import hys.feat_specan_fe2    as adfe2
import hys.feat_specind_clay1 as clay1
import hys.feat_specind_fe1   as fe1
import hys.feat_specan_oc1    as oc1
import hys.feat_specan_oc2    as oc2
import hys.feat_specan_oc3    as oc3
import hys.feat_specind_nsmi  as nsmi
# import hys.feat_specan_smgm   as smgm
import hys.feat_specind_ndgi  as ndgi


def _get_prop(module, wid):
    prop = {}
    prop['mod'] = module
    prop['wid'] = wid
    prop['data'] = None
    prop['bands'] = []
    return prop


class ui_map:

    def __init__(self, parent=None):
        super(ui_map, self).__init__(parent=parent)
    
    def insert_map(self, dname, load_log=False, write_report=False):

        self.map_dname        = dname # directory to store soil product files
        self.map_cube         = None  # input cube data object
        self.map_mask         = None  # input mask data object
        self.map_soil         = {}    # dictionary to store soil product data object
        self.map_write_report = write_report
        
        # =========================================================================================
        # CREATE THE TAB: SOIL MAPPING
        self.gui.widget_tab_page(title = 'Mapping')

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: INPUT
        self.gui.widget_group_box('INPUT')

        # First line
        self.gui.widget_row()
        self.gui.widget_label(text = 'Hyperspectral Data:', width = 170)
        self.gui.widget_text(ID="map_txt_file_pathname")
        self.gui.widget_tool_button(text='...', action=self.map_set_data_pathname)
        self.gui.widget_row_close()

        # second line
        self.gui.widget_row()
        self.gui.widget_label(width=170)
        self.gui.widget_label(width=700, ID="map_lab_file_info")
        self.gui.widget_row_close()

        # Thrid line
        self.gui.widget_row()
        self.gui.widget_label(text = 'Soil Dominant Mask File:', width = 170)
        self.gui.widget_text(ID='map_txt_mask_pathname')
        self.gui.widget_tool_button(text = '...', action=self.map_set_mask_pathname)
        self.gui.widget_tool_button(text = 'Reset', action=self.map_clear_mask_pathname)
        self.gui.widget_row_close()

        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: OUTPUT
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box("OUTPUT")
        self.gui.widget_row()
        self.gui.widget_label(text = 'Soil Directory:', width = 170)
        self.gui.widget_text(ID='map_txt_soil_dir_pathname', text=self.map_dname)
        self.gui.widget_tool_button(text = '...', action=self.map_set_soil_dir_pathname)
        self.gui.widget_row_close()
        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: MAPPING
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box("MAPPING")

        # create the mapping tab
        self.gui.widget_tab()

        self.gui.widget_tab_page("Carbonate")
        self.add_soil("ADC1Check", adc1, 'adc1')
        self.gui.widget_tab_page_close()


        self.gui.widget_tab_page("Clay")
        self.add_soil('ADClay1Check', adclay1, 'adclay1')
        self.add_soil('Clay1Check',   clay1,   'clay1')
        self.gui.widget_tab_page_close()
 
        self.gui.widget_tab_page("Iron")
        self.add_soil('ADFe1Check', adfe1, 'adfe1')
        self.add_soil('ADFe2Check', adfe2, 'adfe2')
        self.add_soil('Fe1Check',   fe1,   'fe1')
        self.gui.widget_tab_page_close()

        self.gui.widget_tab_page("Moisture")
        self.add_soil('NSMICheck', nsmi, 'nsmi')
        # self.add_soil('SMGMCheck', smgm, 'smgm')
        self.gui.widget_tab_page_close()

        self.gui.widget_tab_page("Organic Carbon")
        self.add_soil('OC1Check', oc1, 'oc1')
        self.add_soil('OC2Check', oc2, 'oc2')
        self.add_soil('OC3Check', oc3, 'oc3')
        self.gui.widget_tab_page_close()

        self.gui.widget_tab_page('Gypsum')
        self.add_soil('NSGICheck', ndgi, 'ndgi')
        self.gui.widget_tab_page_close()


        # close the mapping tab
        self.gui.widget_tab_close()
        self.gui.widget_group_box_close()

        self.gui.widget_add_stretch()
        self.gui.widget_group_box('PROCESS', layout="H")
        self.gui.widget_push_button('Run...', action=self.map_exe)
        self.gui.widget_progress(height=10, ID='map_prog_bar')
        if load_log is True:
            self.gui.widget_push_button('Load last log file', action=self.map_load_log)
        self.gui.widget_group_box_close()

        # =========================================================================================
        # CLOSE THE TAB: SOIL MAPPING
        self.gui.widget_tab_page_close()

    # add soil
    def add_soil(self, name, prod, prod_name):
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_push_button('Info', action=self.make_display_info(prod.__info__))
        self.gui.widget_check_button(prod.__gui__, ID=name)
        self.gui.widget_row_close()
        self.map_soil[prod_name] = _get_prop(prod, self.gui.gui[name])
    
    def make_display_info(self, msg):
        def display_info():
            hys.display_information(self, msg)
        return display_info
    



    ###############################################################################################
    #
    # OPEN TO SET A HYPERSPECTRAL DATA FILE PATHNAME
    #
    ###############################################################################################
    def map_set_data_pathname(self):
        title = self.app_name + " - Select a hyperspectral image/spectral library file pathname"
        if self.map_cube is None: dname = os.path.expanduser('~')
        else: dname = os.path.dirname(self.map_cube.fname)
        while True:
            filename = hys.pick_file(self, dname=dname, title=title)
            if filename == "": return # operation canceled
            status, cube = hys.data().open(filename)
            if status is False:
                hys.display_error(self, cube)
                dname = os.path.dirname(filename)
            elif type(cube) != hys.cube and type(cube) != hys.SpectralLibrary:
                msg = os.path.basename(filename) + \
                    "\n is not a valid hyperspectral product: \n" + \
                    "  -> Standard hyperspectral image\n" + \
                    "  -> A spectral library!"
                hys.display_error(self, msg)
                dname = os.path.dirname(filename)
            else:
                break
        self.gui.gui['map_txt_file_pathname'].setText(os.path.basename(filename))
        self.map_cube = cube
        self.gui.gui['map_lab_file_info'].setText(self.map_cube.get_info())
    
    
    
    
    ###############################################################################################
    #
    # OPEN TO SET A MASK FILE PATHNAME
    #
    ###############################################################################################
    def map_set_mask_pathname(self):
        # test if an image is loaded
        if self.map_cube is None:
            msg = "Select a hyperspectral image first"
            hys.display_error(self, msg)
            return

        # test if the image is a spectral library
        if type(self.map_cube) != hys.cube:
            msg = "Soil dominant mask selection works only with hyperspectral image"
            hys.displayinformation(self, msg)
            return

        # set the soil dominant mask file pathname
        title = self.app_name + " - Select a soil dominant mask file pathname"
        if self.map_mask is None: dname = self.map_dname
        else: dname = os.path.dirname(self.map_mask.fname)
        while True:
            filename = hys.pick_file(self, dname=dname, title=title)
            if filename == "": return 
            status, mask = hys.data().open(filename)
            if status is False:
                hys.display_error(self, mask)
                dname = os.path.dirname(filename)
            elif type(mask) != hys.mask:
                msg = os.path.basename(filename) + "\nis not a valid mask file"
                hys.display_error(self, msg)
                mask = None
                dname = os.path.dirname(filename)
            elif self.map_cube.samples != mask.samples or self.map_cube.lines != mask.lines:
                msg = os.path.basename(filename) + "\nmask dimensions do not fit with image dimensions"
                hys.display_error(self, msg)
                mask = None
                dname = os.path.dirname(filename)
            else: break
        self.map_mask = mask
        self.gui.gui['map_txt_mask_pathname'].setText(os.path.basename(self.map_mask.fname))




    ###############################################################################################
    #
    # RESET THE FIELD OF THE MASK
    #
    ###############################################################################################
    def map_clear_mask_pathname(self):
        if self.map_cube is None: return
        if self.map_mask is None: return
        do_it = QMessageBox.question(
            self,
            self.app_name,
            "Do you want to reset the mask field?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if do_it == QMessageBox.No: return
        self.map_mask = None
        self.gui.gui['map_txt_mask_pathname'].setText("")




    ###############################################################################################
    #
    # SET A SOIL FEATURE DIRECTORY PATHNAME
    #
    ###############################################################################################
    def map_set_soil_dir_pathname(self):
        title = self.app_name + " - Select a soil feature directory pathname"
        dname = hys.pick_file(self, title=title, dname=self.map_dname, directory=True)
        if dname == "": return
        if not os.access(dname, os.W_OK):
            msg = dname + "\n is not writable"
            hys.display_error(self, msg)
            return
        self.map_dname = dname
        self.gui.gui['map_txt_soil_dir_pathname'].setText(dname)




    ###############################################################################################
    #
    # CALCULATE SOIL FEATURES
    #
    ###############################################################################################
    def map_exe(self):
        # check input data
        if self.map_cube is None:
            msg = "Select a hyperspectral data file first"
            hys.display_error(self, msg)
            return
        
        # determine root filename
        rname = os.path.basename((os.path.splitext(self.map_cube.fname))[0])

        # create the report file
        if self.map_write_report is True:
            report = hys.report(self.map_dname + os.path.sep + rname)

        # Check is soil feature map(s) will be calculated
        n_soil = 0
        flag_no_soil=True
        wvl = np.asarray(self.map_cube.meta.get('wavelength'), dtype='f4')
        for key, item in self.map_soil.items():
            if item['wid'].isChecked() is False: continue
            flag_no_soil = False
            if self.map_write_report is True: report.add_product(key, item['mod'].__gui__)
            ind, st = self.map_cube.select_bands(item['mod'].__bands__)
            if self.map_write_report is True: report.set_product_lit_bands(key, item['mod'].__bands__)
            if st is False:
                if self.map_write_report is True: report.set_product_status(key, "No band found!")
                item['wid'].setChecked(False)
                continue
            st, msg = item['mod'].check_bands(ind, wvl)
            if self.map_write_report is True: report.set_product_sel_bands(key, wvl[ind])
            if st is False:
                if self.map_write_report is True: report.set_product_status(key, msg)
                item['wid'].setChecked(False)
                continue
            if self.map_write_report is True: report.set_product_status(key, msg)
            item['bands'] = ind
            pname = self.map_dname + os.path.sep + rname + item['mod'].__filename__ + ".dat"
            oprod = hys.product(fname=pname, src=self.map_cube, tile=True)
            item['data'] = oprod
            n_soil += 1
        if self.map_write_report is True: report.write_product()
        if n_soil == 0:
            msg  = "No soil map feature might been calculated!\n" 
            if self.map_write_report is True: msg += "Please have a look to the last log file"
            hys.display_error(self, msg)
            if self.map_write_report is True:
                if flag_no_soil: 
                    report.add_information("No soil feature has been selected!\n\n")
                    report.done()
            
        # write report concerning the selection of a mask (if desired)
        if self.map_write_report is True:
            if self.map_mask is None:
                if type(self.map_cube) is hys.SpectralLibrary:
                    report.add_information("No mask necessary for spectral library")
                else:
                    report.add_information("No mask has been selected!")
            else:
                report.add_information("Selected mask is: " + self.map_mask.fname)
        
        # generate tile for input data
        self.map_cube.tile_data()
        if self.map_mask is not None: self.map_mask.tile_data()

        # intialize the loop
        t1 = time.time()
        self.gui.gui['map_prog_bar'].setMinimum(0)
        self.gui.gui['map_prog_bar'].setMaximum(self.map_cube.bn)

        # loop of tiles
        for k in range(self.map_cube.bn):
            self.gui.gui['map_prog_bar'].setValue(k+1)
            im = self.map_cube.read(tile=k)
            mk = np.ones((im.shape[1], im.shape[2]), dtype=np.int32)
            if self.map_mask is not None:
                mk = self.map_mask.read(tile=k)
                mk = np.reshape(mk, (mk.shape[1], mk.shape[2]))
            for key, item in self.map_soil.items():
                if item['wid'].isChecked() is False: continue
                ind = np.asarray(item['bands'])
                prod = item['mod'].process(im, wvl, ind, mk)
                item['data'].write(np.asarray(prod), tile=k)
        msg = "Processing complete in %8.2f seconds"%(time.time()-t1)
        hys.display_information(self, msg)
        if self.map_write_report:
            report.add_information("\n" + msg + "\n")
            report.done()
        self.gui.gui['map_prog_bar'].setValue(0)




    ###############################################################################################
    #
    # OPTIONAL: LOAD LAST LOG FILE
    #
    ###############################################################################################
    def map_load_log(self):
        # get all files in soil directory
        f = os.listdir(self.map_dname)
        flog = []
        tlog = []
        for doc in f:
            if doc.endwith(".log"):
                flog.append(doc)
                tlog.append(os.path.getctime(self.map_dname + os.path.sep + doc))
        if len(flog) == 0:
            hys.display_information(self, "No log file found!")
            return
        flog = flog[tlog.index(max(tlog))]
        txt = open(self.map_dname + os.path_sep + flog, 'r').read()
        self.map_display_text = hys.displayText(flog, txt)








        
        