# -*- coding: utf-8 -*-
#
# Copyright © 2019 / Dr. Stéphane Guillaso
# Licensed under the terms of the 
# (see ../LICENSE.md for details)

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
import numpy as np
import time
import hys
import os

import hys.mask_specind_ndrbi as ndrbi
import hys.mask_specind_ndvi  as ndvi
import hys.mask_specind_ncai  as ncai


class ui_msk:

    def __init__(self, parent=None):
        super(ui_msk, self).__init__(parent=parent)
    
    def insert_msk(self, dname):

        self.msk_dname = self.map_dname # directory to store soil product files
        self.msk_cube  = None  # input cube data object
        self.msk_mask  = None  # input mask data object
        self.msk_rname = ""
        
        # =========================================================================================
        # CREATE THE TAB: SOIL MASKING
        self.gui.widget_tab_page(title = 'Masking')

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: INPUT
        self.gui.widget_group_box('INPUT')

        # First line
        self.gui.widget_row()
        self.gui.widget_label(text = 'Hyperspectral Data:', width = 170)
        self.gui.widget_text(ID="msk_txt_file_pathname")
        self.gui.widget_tool_button(text='...', action=self.msk_set_data_pathname)
        self.gui.widget_tool_button(text='Get', action=self.msk_get_data_pathname)
        self.gui.widget_row_close()

        # second line
        self.gui.widget_row()
        self.gui.widget_label(width=170)
        self.gui.widget_label(width=700, ID="msk_lab_file_info")
        self.gui.widget_row_close()

        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: OUTPUT
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box("OUTPUT")
        self.gui.widget_row()
        self.gui.widget_label(text = 'Soil Mask Directory:', width = 170)
        self.gui.widget_text(ID='msk_txt_mask_dir_pathname', text=self.msk_dname)
        self.gui.widget_tool_button(text='...', action=self.msk_set_mask_dir_pathname)
        self.gui.widget_tool_button(text='Get', action=self.msk_get_mask_dir_pathname)
        self.gui.widget_row_close()
        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: METHODS
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box("METHODS")

        # NDRBI
        self.gui.widget_row()
        self.gui.widget_check_button('Mask water areas using NDRBI:', ID='msk_set_ndrbi', width = 270, action=self.msk_select_ndrbi)
        self.gui.widget_text(ID='msk_ndrbi')
        self.gui.widget_row_close()

        # NDVI
        self.gui.widget_row()
        self.gui.widget_check_button('Mask green vegetated areas using NDVI:', ID='msk_set_ndvi', width = 270, action=self.msk_select_ndvi)
        self.gui.widget_text(ID = 'msk_ndvi')
        self.gui.widget_row_close()

        # NCAI
        self.gui.widget_row()
        self.gui.widget_check_button('Mask dry vegetated areas using NCAI:', ID='msk_set_ncai', width = 270, action=self.msk_select_ncai)
        self.gui.widget_text(ID = 'msk_ncai')
        self.gui.widget_row_close()

        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: INFORMATION
        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box('INFORMATION')
        self.gui.widget_label(ID='msk_info_line_1', height=27)
        self.gui.widget_label(ID='msk_info_line_2', height=27)
        self.gui.widget_group_box_close()

        # -----------------------------------------------------------------------------------------
        # GROUP BOX: PROCESS
        self.gui.widget_add_stretch()
        self.gui.widget_group_box('PROCESS', layout='H')
        self.gui.widget_push_button('Run...', action=self.msk_exe)
        self.gui.widget_progress(height=10, ID='msk_prog_bar')
        self.gui.widget_push_button("Export", action=self.msk_export)
        self.gui.widget_group_box_close()


        # =========================================================================================
        # CLOSE THE TAB: SOIL MAPPING
        self.gui.widget_tab_page_close()

    # # add soil
    # def add_soil(self, name, prod, prod_name):
    #     self.gui.widget_row(alignment=Qt.AlignLeft)
    #     self.gui.widget_push_button('Info', action=self.make_display_info(prod.__info__))
    #     self.gui.widget_check_button(prod.__gui__, ID=name)
    #     self.gui.widget_row_close()
    #     self.map_soil[prod_name] = _get_prop(prod, self.gui.gui[name])
    
    # def make_display_info(self, msg):
    #     def display_info():
    #         hys.display_information(self, msg)
    #     return display_info
    
    def msk_update_rname(self):
        if self.msk_cube is None:
            return
        self.msk_rname = os.path.basename((os.path.splitext(self.msk_cube.fname))[0])
        self.msk_select_ndrbi()
        self.msk_select_ndvi()
        self.msk_select_ncai()




    ###############################################################################################
    #
    # OPEN TO SET A HYPERSPECTRAL DATA FILE PATHNAME
    #
    ###############################################################################################
    def msk_set_data_pathname(self):
        title = self.app_name + " - Select a hyperspectral image/spectral library file pathname"
        if self.msk_cube is None: dname = os.path.expanduser('~')
        else: dname = os.path.dirname(self.msk_cube.fname)
        while True:
            filename = hys.pick_file(self, dname=dname, title=title)
            if filename == "": return # operation canceled
            status, cube = hys.data().open(filename)
            if status is False:
                hys.display_error(self, cube)
                dname = os.path.dirname(filename)
            elif type(cube) != hys.cube:
                msg = os.path.basename(filename) + "\n is not a hyperspectral image " 
                hys.display_error(self, msg)
                dname = os.path.dirname(filename)
            else:
                break
        self.gui.gui['msk_txt_file_pathname'].setText(os.path.basename(filename))
        self.msk_cube = cube
        self.gui.gui['msk_lab_file_info'].setText(self.msk_cube.get_info())
        self.msk_update_rname()




    ###############################################################################################
    #
    # IMPORT HYPERSPECTRAL DATA FROM MAPPING PAGE
    #
    ###############################################################################################
    def msk_get_data_pathname(self):
        if self.map_cube is None:
            msg = "No hyperspectral product has been load!"
            hys.display_error(self, msg)
            return
        if type(self.map_cube) == hys.SpectralLibrary:
            msg = self.map_cube.fname + "\n is a spectral library!"
            hys.display_information(self, msg)
            return
        self.msk_cube = self.map_cube
        self.gui.gui['msk_txt_file_pathname'].setText(os.path.basename(self.msk_cube.fname))
        self.gui.gui['msk_lab_file_info'].setText(self.msk_cube.get_info())
        self.msk_update_rname()




    ###############################################################################################
    #
    # SET A SOIL MASK DIRECTORY PATHNAME
    #
    ###############################################################################################
    def msk_set_mask_dir_pathname(self):
        title = self.app_name + " - Select a soil mask directory pathname"
        dname = hys.pick_file(self, title=title, dname=self.map_dname, directory=True)
        if dname == "": return
        if not os.access(dname, os.W_OK):
            msg = dname + "\n is not writable"
            hys.display_error(self, msg)
            return
        self.msk_dname = dname
        self.gui.gui['msk_txt_mask_dir_pathname'].setText(dname)




    ###############################################################################################
    #
    # IMPORT A SOIL MASK DIRECTORY PATHNAME
    #
    ###############################################################################################
    def msk_get_mask_dir_pathname(self):
        self.msk_dname = self.map_dname
        self.gui.gui['msk_txt_mask_dir_pathname'].setText(self.msk_dname)




    ###############################################################################################
    #
    # SELECT NDRBI
    #
    ###############################################################################################
    def msk_select_ndrbi(self):
        if self.msk_cube is None:
            hys.display_error(self, "Select a hyperspectral product first")
            self.gui.gui['msk_set_ndrbi'].setChecked(False)
            return
        msg = ""
        if self.gui.gui['msk_set_ndrbi'].isChecked():
            msg = self.msk_rname + "_water.dat; " + self.msk_rname + "_water_mask.dat;"
        self.gui.gui['msk_ndrbi'].setText(msg)
        self.msk_display_information()




    ###############################################################################################
    #
    # SELECT NDVI
    #
    ###############################################################################################
    def msk_select_ndvi(self):
        if self.msk_cube is None:
            hys.display_error(self, "Select a hyperspectral product first")
            self.gui.gui['msk_set_ndvi'].setChecked(False)
            return
        msg = ""
        if self.gui.gui['msk_set_ndvi'].isChecked():
            msg = self.msk_rname + "_NDVI.dat; " + self.msk_rname + "_NDVI_mask.dat;"
        self.gui.gui['msk_ndvi'].setText(msg)
        self.msk_display_information()




    ###############################################################################################
    #
    # SELECT NCAI
    #
    ###############################################################################################
    def msk_select_ncai(self):
        if self.msk_cube is None:
            hys.display_error(self, "Select a hyperspectral product first")
            self.gui.gui['msk_set_ncai'].setChecked(False)
            return
        msg = ""
        if self.gui.gui['msk_set_ncai'].isChecked():
            msg = self.msk_rname + "_NCAI.dat; " + self.msk_rname + "_NCAI_mask.dat;"
        self.gui.gui['msk_ncai'].setText(msg)
        self.msk_display_information()




    ###############################################################################################
    #
    # DISPLAY INFORMATION
    #
    ###############################################################################################
    def msk_display_information(self):
        sm = np.zeros(3, dtype='i2')
        if self.gui.gui['msk_set_ndrbi'].isChecked(): sm[0] = 1
        if self.gui.gui['msk_set_ndvi'].isChecked():  sm[1] = 1
        if self.gui.gui['msk_set_ncai'].isChecked():  sm[2] = 1
        ind = np.where(sm == 1)
        msg = ""
        if np.size(ind[0]) > 0:
            msg = "Generate the file: " + self.msk_rname + "_soildom_mask.dat"
        self.gui.gui['msk_info_line_1'].setText(msg)
        msg = ""
        if np.size(ind[0]) == 1:
            msg = "It will be equal to the mask provided by "
        if np.size(ind[0]) > 1:
            msg = "It will consist of the logical sum of masks provided by "
        if np.size(ind[0]) == 1:
            if sm[0] == 1: msg += 'NDRBI'
            if sm[1] == 1: msg += 'NDVI'
            if sm[2] == 1: msg += 'NCAI'
        if np.size(ind[0]) == 2:
            if sm[0]==1 and sm[1] == 1: msg += 'NDRBI + NDVI'
            if sm[0]==1 and sm[2] == 1: msg += 'NDRBI + NCAI'
            if sm[1]==1 and sm[2] == 1: msg += 'NDVI + NCAI'
        if np.size(ind[0]) == 3:
            msg += 'NDRBI + NDVI + NCAI'
        self.gui.gui['msk_info_line_2'].setText(msg)




    ###############################################################################################
    #
    # CALCULATE SOIL MASKS INCLUDING SOIL DOMINANT MASK
    #
    ###############################################################################################
    def msk_exe(self):
        # check input data
        if self.msk_cube is None:
            msg = "Select a hyperspectral image file first"
            hys.display_error(self, msg)
            return
        
        nmask = 0
        vWater = self.gui.gui['msk_set_ndrbi'].isChecked()
        vNDVI  = self.gui.gui['msk_set_ndvi'].isChecked()
        vNCAI  = self.gui.gui['msk_set_ncai'].isChecked()
        if not vWater and not vNDVI and not vNCAI:
            msg = "Select at least a soil mask"
            hsy.display_error(self, msg)
            return
        
        # calculate tile
        self.msk_cube.tile_data()

        # define output filename
        dname = self.msk_dname + os.path.sep

        # intialize the progress bar
        t1 = time.time()
        self.gui.gui['msk_prog_bar'].setMinimum(0)
        self.gui.gui['msk_prog_bar'].setMaximum(self.msk_cube.bn)

        # erase the second line
        self.gui.gui['msk_info_line_2'].setText("")

        # select bands for the different products
        if vWater:
            bind_water, st = self.msk_cube.select_bands(ndrbi.__bands__)
            if st:
                pname = dname + self.msk_rname + ndrbi.__filename__ + ".dat"
                mname = dname + self.msk_rname + ndrbi.__filename__ + "_mask.dat"
                p_water = hys.product(fname=pname, src=self.msk_cube, tile=True)
                m_water = hys.mask(fname=mname, src=self.msk_cube, tile=True)
            else:
                vWater = False
        if vNDVI:
            bind_ndvi, st = self.msk_cube.select_bands(ndvi.__bands__)
            if st:
                pname = dname + self.msk_rname + ndvi.__filename__ + ".dat"
                mname = dname + self.msk_rname + ndvi.__filename__ + "_mask.dat"
                p_ndvi = hys.product(fname=pname, src=self.msk_cube, tile=True)
                m_ndvi = hys.mask(fname=mname, src=self.msk_cube, tile=True)
            else:
                vNDVI = False
        if vNCAI:
            bind_ncai, st = self.msk_cube.select_bands(ncai.__bands__)
            if st:
                pname = dname + self.msk_rname + ncai.__filename__ + ".dat"
                mname = dname + self.msk_rname + ncai.__filename__ + "_mask.dat"
                p_ncai = hys.product(fname=pname, src=self.msk_cube, tile=True)
                m_ncai = hys.mask(fname=mname, src=self.msk_cube, tile=True)
            else:
                vNCAI = False
        
        # if all test failed
        if not vWater and not vNDVI and not vNCAI:
            msg  = "There is a problem extracting bands for all products\n"
            msg += "Check you product!"
            hys.display_error(self, msg)
            return
        
        # define the soil dominant mask
        mname = dname + self.msk_rname + "_soildom_mask.dat"
        self.msk_mask = hys.mask(fname=mname, src=self.msk_cube, tile=True)

        # loop over the data tiles
        for k in range(self.msk_cube.bn):
            self.gui.gui['msk_prog_bar'].setValue(k+1)
            im = self.msk_cube.read(tile=k)
            omsk = np.ones((im.shape[1], im.shape[2]), dtype=np.int16)
            if vWater:
                prod, mask = ndrbi.process(im[bind_water, :, :])
                p_water.write(np.asarray(prod), tile=k)
                m_water.write(np.asarray(mask).astype(np.int16), tile=k)
                omsk *= np.asarray(mask).astype(np.int16)
            if vNDVI:
                prod, mask = ndvi.process(im[bind_ndvi, :, :])
                p_ndvi.write(np.asarray(prod), tile=k)
                m_ndvi.write(np.asarray(mask).astype(np.int16), tile=k)
                omsk *= np.asarray(mask).astype(np.int16)
            if vNCAI:
                prod, mask = ncai.process(im[bind_ncai, :, :])
                p_ncai.write(np.asarray(prod), tile=k)
                m_ncai.write(np.asarray(mask).astype(np.int16), tile=k)
                omsk *= np.asarray(mask).astype(np.int16)
            self.msk_mask.write(omsk, tile=k)
        
        # ipdate information
        msg = "Processing complete in %8.2f seconds"%(time.time() - t1)
        hys.display_information(self, msg)
        self.gui.gui['msk_prog_bar'].setValue(0)




    ###############################################################################################
    #
    # EXPORT SOIL MASK TO MAP TAB
    #
    ###############################################################################################
    def msk_export(self):
        if self.msk_mask is None:
            msg = "Create a soil dominant mask first"
            hys.display_error(self, msg)
            return
        self.map_mask = self.msk_mask
        self.gui.gui['map_txt_mask_pathname'].setText(os.path.basename(self.map_mask.fname))
