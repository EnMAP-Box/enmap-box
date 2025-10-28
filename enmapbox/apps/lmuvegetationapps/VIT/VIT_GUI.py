# -*- coding: utf-8 -*-

# This module handles the GUI of the Vegetation Index Toolbox

import sys

import lmuvegetationapps.VIT.VIT_core
from _classic.hubflow.core import *
from enmapbox.gui.utils import loadUi
from lmuvegetationapps import APP_DIR
from qgis.PyQt.QtWidgets import *
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsMapLayerComboBox

# import os

pathUI_vit = os.path.join(APP_DIR, 'Resources/UserInterfaces/VIT.ui')
pathUI_nodat = os.path.join(APP_DIR, 'Resources/UserInterfaces/Nodat.ui')
pathUI_prgbar = os.path.join(APP_DIR, 'Resources/UserInterfaces/ProgressBar.ui')


class VIT_GUI(QDialog):
    mLayer: QgsMapLayerComboBox

    def __init__(self, parent=None):
        super(VIT_GUI, self).__init__(parent)
        loadUi(pathUI_vit, self)

        from enmapbox.gui.enmapboxgui import EnMAPBox
        emb = EnMAPBox.instance()
        if isinstance(emb, EnMAPBox):
            self.mLayer.setProject(emb.project())

        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)


class NodatGUI(QDialog):
    def __init__(self, parent=None):
        super(NodatGUI, self).__init__(parent)
        loadUi(pathUI_nodat, self)


class PRG_GUI(QDialog):
    def __init__(self, parent=None):
        super(PRG_GUI, self).__init__(parent)
        loadUi(pathUI_prgbar, self)

        self.allow_cancel = False

    def closeEvent(self, event):
        # window may only be closed, if self.allow_cancel is TRUE (=Cancel Button hit)
        if self.allow_cancel:
            event.accept()
        else:
            event.ignore()


# class VIT handels the Toolbox-GUI itself
class VIT:
    def __init__(self, main):
        self.main = main
        self.gui = VIT_GUI()

        self.checkboxes = self.gui.findChildren(QCheckBox)  # all Checkboxes in the GUI
        self.dictchecks()  # connect checkboxes to dictionary
        self.connections()
        self.initial_values()

    def initial_values(self):
        self.image, self.outFileName, self.outExtension, self.outDir = None, None, None, None
        self.interpolation_type = 1  # Interpolation type: 1: NN, 2: linear, 3: IDW
        self.idw_exp = 2  # exponent of IDW interpolation
        self.out_single = 1  # 1: output to single file; else: output to individual files
        self.structIndices = [-1] * 13  # preset all indices in groups and set their flags to -1 (off)
        self.chlIndices = [-1] * 26
        self.carIndices = [-1] * 5
        self.watIndices = [-1] * 8
        self.dmIndices = [-1] * 10
        self.flIndices = [-1] * 4
        self.nodat = [-999, -999]  # nodat[0] = in, nodat[1] = out
        self.division_factor = 1.0
        self.addItem = []
        self.gui.mLayer.setLayer(None)

    def connections(self):
        self.gui.cmdSelectAll.clicked.connect(lambda: self.check(bool_check=True))
        self.gui.cmdDeselectAll.clicked.connect(lambda: self.check(bool_check=False))
        self.gui.cmdOK.clicked.connect(lambda: self.run_vit())
        self.gui.cmdInputImage.clicked.connect(lambda: self.open_file(mode="imgSelect"))
        self.gui.mLayer.layerChanged.connect(lambda: self.open_file(mode="imgDropdown"))
        self.gui.cmdOutputImage.clicked.connect(lambda: self.open_file(mode="output"))
        self.gui.cmdCancel.clicked.connect(lambda: self.exit_gui())

        self.gui.radNN.toggled.connect(lambda: self.toggle_interpol())
        self.gui.radLinear.toggled.connect(lambda: self.toggle_interpol())
        self.gui.radIDW.toggled.connect(lambda: self.toggle_interpol())
        self.gui.spinIDW_exp.valueChanged.connect(lambda: self.toggle_interpol())

        self.gui.radSingle.toggled.connect(lambda: self.toggle_write())
        self.gui.radIndiv.toggled.connect(lambda: self.toggle_write())

        # assign checkboxes to function: select/deselect on click
        for ind in self.dict_structural:
            self.dict_structural[ind].stateChanged.connect(lambda group, iid=ind: self.toggles(group="structural",
                                                                                               cid=iid))
        for ind in self.dict_chl:
            self.dict_chl[ind].stateChanged.connect(lambda group, iid=ind: self.toggles(group="chl",
                                                                                        cid=iid))
        for ind in self.dict_caranth:
            self.dict_caranth[ind].stateChanged.connect(lambda group, iid=ind: self.toggles(group="caranth",
                                                                                            cid=iid))
        for ind in self.dict_wat:
            self.dict_wat[ind].stateChanged.connect(lambda group, iid=ind: self.toggles(group="water",
                                                                                        cid=iid))
        for ind in self.dict_drymat:
            self.dict_drymat[ind].stateChanged.connect(lambda group, iid=ind: self.toggles(group="drymat",
                                                                                           cid=iid))
        for ind in self.dict_fluor:
            self.dict_fluor[ind].stateChanged.connect(lambda group, iid=ind: self.toggles(group="fluor",
                                                                                          cid=iid))

    def toggles(self, group, cid):
        # *= -1 is a switch on/off
        if group == "structural":
            self.structIndices[cid] *= -1
        elif group == "chl":
            self.chlIndices[cid] *= -1
        elif group == "caranth":
            self.carIndices[cid] *= -1
        elif group == "water":
            self.watIndices[cid] *= -1
        elif group == "drymat":
            self.dmIndices[cid] *= -1
        elif group == "fluor":
            self.flIndices[cid] *= -1

    def dictchecks(self):
        # a dictionary for all the checkboxes, so they can be addressed in functions
        self.dict_structural = {0: self.gui.box_hndvi_opp, 1: self.gui.box_ndvi_apa, 2: self.gui.box_ndvi_dat,
                                3: self.gui.box_ndvi_hab, 4: self.gui.box_ndvi_zar, 5: self.gui.box_mcari1,
                                6: self.gui.box_mcari2, 7: self.gui.box_msavi, 8: self.gui.box_mtvi1,
                                9: self.gui.box_mtvi2, 10: self.gui.box_osavi, 11: self.gui.box_rdvi,
                                12: self.gui.box_spvi}

        self.dict_chl = {0: self.gui.box_csi1, 1: self.gui.box_csi2, 2: self.gui.box_gi, 3: self.gui.box_gitmer1,
                         4: self.gui.box_gitmer2, 5: self.gui.box_gndvi, 6: self.gui.box_mcari, 7: self.gui.box_npqi,
                         8: self.gui.box_pri, 9: self.gui.box_reip, 10: self.gui.box_rep, 11: self.gui.box_srch1,
                         12: self.gui.box_sr705, 13: self.gui.box_tcari, 14: self.gui.box_tvi, 15: self.gui.box_vog1,
                         16: self.gui.box_vog2, 17: self.gui.box_ztm, 18: self.gui.box_sra, 19: self.gui.box_srb1,
                         20: self.gui.box_srb2, 21: self.gui.box_srtot, 22: self.gui.box_pssra, 23: self.gui.box_pssrb,
                         24: self.gui.box_lci, 25: self.gui.box_mlo}

        self.dict_caranth = {0: self.gui.box_ari, 1: self.gui.box_cri1, 2: self.gui.box_cri2, 3: self.gui.box_pssrc,
                             4: self.gui.box_sipi}

        self.dict_wat = {0: self.gui.box_dswi, 1: self.gui.box_dswi5, 2: self.gui.box_lwvi1, 3: self.gui.box_lwvi2,
                         4: self.gui.box_msi, 5: self.gui.box_ndwi, 6: self.gui.box_pwi, 7: self.gui.box_srwi}

        self.dict_drymat = {0: self.gui.box_swirvi, 1: self.gui.box_cai, 2: self.gui.box_ndli, 3: self.gui.box_ndni,
                            4: self.gui.box_bgi, 5: self.gui.box_bri, 6: self.gui.box_rgi, 7: self.gui.box_srpi,
                            8: self.gui.box_npci, 9: self.gui.box_ndi_test}

        self.dict_fluor = {0: self.gui.box_cur, 1: self.gui.box_lic1, 2: self.gui.box_lic2, 3: self.gui.box_lic3}

    def check(self, bool_check):
        # select/deselect checkboxes (all)
        for i in range(len(self.dict_structural)):
            self.dict_structural[i].setChecked(bool_check)
        for i in range(len(self.dict_chl)):
            self.dict_chl[i].setChecked(bool_check)
        for i in range(len(self.dict_caranth)):
            self.dict_caranth[i].setChecked(bool_check)
        for i in range(len(self.dict_wat)):
            self.dict_wat[i].setChecked(bool_check)
        for i in range(len(self.dict_drymat)):
            self.dict_drymat[i].setChecked(bool_check)
        for i in range(len(self.dict_fluor)):
            self.dict_fluor[i].setChecked(bool_check)

    def toggle_interpol(self):
        # Switch interpolation types
        if self.gui.radNN.isChecked():
            self.interpolation_type = 1
            self.gui.spinIDW_exp.setDisabled(True)
        elif self.gui.radLinear.isChecked():
            self.interpolation_type = 2
            self.gui.spinIDW_exp.setDisabled(True)
        else:
            self.interpolation_type = 3
            self.gui.spinIDW_exp.setDisabled(False)
            self.idw_exp = self.gui.spinIDW_exp.value()

    def toggle_write(self):
        # Switch output file type
        if self.gui.radSingle.isChecked():
            self.out_single = 1
        else:
            self.out_single = 0

    def open_file(self, mode):
        if mode == "imgSelect":
            if self.image is not None:
                self.image = None
            bsq_input = QFileDialog.getOpenFileName(caption='Select Input Image', filter="ENVI Image (*.bsq)")[0]
            if not bsq_input:
                return
            self.addItem.append(bsq_input)
            self.gui.mLayer.setAdditionalItems(self.addItem)
            self.gui.mLayer.setCurrentText(bsq_input)

            self.image = bsq_input
            self.image_read()

        elif mode == "imgDropdown":
            if self.image is not None:
                self.image = None
            if self.gui.mLayer.currentLayer() is not None:
                input = self.gui.mLayer.currentLayer()
                bsq_input = input.source()
            elif len(self.gui.mLayer.currentText()) > 0:
                bsq_input = self.gui.mLayer.currentText()
            else:
                self.image = None
                return
            self.image = bsq_input
            self.image_read()

        elif mode == "output":
            out_file = QFileDialog.getSaveFileName(caption='Select Output File', filter="ENVI Image (*.bsq)")[0]
            if not out_file:
                return
            self.gui.txtOutputImage.setText(out_file)
            try:
                _, self.outExtension = os.path.splitext(out_file)
                self.outFileName = os.path.basename(out_file)
            except:
                self.outExtension = '.bsq'
                self.outFileName = os.path.basename(out_file)
                print(self.outFileName)
            self.outDir = os.path.dirname(out_file) + "/"  # outDir ends with / so that a filename can be string-added

    def image_read(self):
        try:
            meta = self.get_image_meta(image=self.image, image_type="Input Image")
            self.dtype = meta[4]
            if self.dtype < 4 or self.dtype > 9:
                QMessageBox.information(self.gui, "Integer Input",
                                        "Integer input image:\nTool requires float [0.0-1.0]:\nDivision factor set to 10000")
                self.division_factor = 10000
                self.gui.txtDivisionFactor.setText(str(self.division_factor))
        except ValueError as e:
            self.abort(message=str(e))
            return
        if None in meta:
            self.image = None
            self.nodat[0] = None
            return
        else:
            self.gui.lblNodatImage.setText(str(meta[0]))
            self.gui.txtNodatOutput.setText(str(meta[0]))
            self.nodat[0] = meta[0]

    def get_image_meta(self, image, image_type):
        dataset = openRasterDataset(image)
        if dataset is None:
            raise ValueError(
                '%s could not be read. Please make sure it is a valid ENVI image' % image_type)
        else:
            metadict = dataset.metadataDict()

            nrows = int(metadict['ENVI']['lines'])
            ncols = int(metadict['ENVI']['samples'])
            nbands = int(metadict['ENVI']['bands'])
            dtype = int(metadict['ENVI']['data type'])
            if nbands < 2:
                raise ValueError("Input is not a multi-band image")
            try:
                nodata = int(metadict['ENVI']['data ignore value'])
                return nodata, nbands, nrows, ncols, dtype
            except:
                self.main.nodat_widget.init(image_type=image_type, image=image)
                self.main.nodat_widget.gui.setModal(True)  # parent window is blocked
                self.main.nodat_widget.gui.exec_()  # unlike .show(), .exec_() waits with execution of the code, until the app is closed
                return self.main.nodat_widget.nodat, nbands, nrows, ncols, dtype

    def exit_gui(self):
        self.gui.close()  # I wonder what this does...

    def abort(self, message):
        QMessageBox.critical(self.gui, "Error", message)

    def run_vit(self):
        if self.image is None:
            QMessageBox.critical(self.gui, "No image selected", "Please select an image to continue!")
            return
        elif self.outFileName is None:
            QMessageBox.critical(self.gui, "No output file selected", "Please select an output file for your image!")
            return
        elif self.gui.txtNodatOutput.text() == "":
            QMessageBox.critical(self.gui, "No Data Value", "Please specify No Data Value!")
            return
        else:
            try:
                self.nodat[1] = int(self.gui.txtNodatOutput.text())
            except ValueError:
                QMessageBox.critical(self.gui, "Error", "'%s' is not a valid  No Data Value!" %
                                     self.gui.txtNodatOutput.text())
                return
        try:
            self.division_factor = float(self.gui.txtDivisionFactor.text())
        except ValueError:
            QMessageBox.critical(self.gui, "Error", "'%s' is not a valid division factor!" %
                                 self.gui.txtDivisionFactor.text())
            return

        # initialize VIT
        vit = lmuvegetationapps.VIT.VIT_core.VIT(interpolation_type=self.interpolation_type, idw_exp=self.idw_exp,
                                                 nodat=self.nodat, division_factor=self.division_factor)

        # check and pass all indices that were selected
        vit.toggle_indices(StructIndices=self.structIndices, ChlIndices=self.chlIndices, CarIndices=self.carIndices,
                           WatIndices=self.watIndices, DmIndices=self.dmIndices, FlIndices=self.flIndices)

        if not vit.n_indices > 0:
            QMessageBox.critical(self.gui, "No index selected", "Please select at least one index to continue!")
            return

        # show progressbar - window
        self.main.prg_widget.gui.lblCaption_l.setText("Vegetation Indices Toolbox")
        self.main.prg_widget.gui.lblCaption_r.setText("Reading Input Image...this may take several minutes")
        self.main.prg_widget.gui.prgBar.setValue(0)
        self.main.prg_widget.gui.setModal(True)
        self.main.prg_widget.gui.show()
        self.main.prg_widget.gui.allow_cancel = True  # The window may be cancelled
        self.main.qgis_app.processEvents()

        try:
            image_in_matrix = vit.read_image(self.image)  # read the image
        except ValueError as e:
            QMessageBox.critical(self.gui, 'error', str(e))
            self.main.prg_widget.gui.allow_cancel = True  # The window may be cancelled
            self.main.prg_widget.gui.close()
            return

        if image_in_matrix is None:
            QMessageBox.critical(self.gui, "Image unreadable", "The image file could not be read.")
            return

        vit.prepare_indices()

        self.main.prg_widget.gui.lblCaption_r.setText("Preparing Indices")
        self.main.qgis_app.processEvents()

        try:
            index_out_matrix = vit.calculate_VIT(prg_widget=self.main.prg_widget,
                                                 qgis_app=self.main.qgis_app)
        except:
            QMessageBox.critical(self.gui, 'error', "An unspecific error occured.")
            self.main.prg_widget.gui.allow_cancel = True
            self.main.prg_widget.gui.close()
            return

        self.main.prg_widget.gui.lblCaption_r.setText("Writing Output-File")
        self.main.qgis_app.processEvents()

        # try:
        vit.write_out(index_out_matrix=index_out_matrix, out_dir=self.outDir, out_filename=self.outFileName,
                      out_single=self.out_single)
        # except:
        #     QMessageBox.critical(self.gui, 'error', "An unspecific error occured while trying to write image data")
        #     self.main.prg_widget.gui.allow_cancel = True
        #     return

        self.main.prg_widget.gui.allow_cancel = True
        self.main.prg_widget.gui.close()
        QMessageBox.information(self.gui, "Finish", "Calculation of indices finished")
        # self.gui.close()


# GUI-specifications for NoData-Dialog
class Nodat:
    def __init__(self, main):
        self.main = main
        self.gui = NodatGUI()
        self.connections()
        self.image = None

    def init(self, image_type, image):
        topstring = '%s @ %s' % (image_type, image)
        self.gui.lblSource.setText(topstring)
        self.gui.txtNodat.setText("")
        self.image = image
        self.nodat = None

    def connections(self):
        self.gui.cmdCancel.clicked.connect(lambda: self.gui.close())
        self.gui.cmdOK.clicked.connect(lambda: self.ok())

    def ok(self):
        if self.gui.txtNodat.text() == "":
            QMessageBox.critical(self.gui, "No Data", "A no data value must be supplied for this image!")
            return
        else:
            try:
                nodat = int(self.gui.txtNodat.text())
            except:
                QMessageBox.critical(self.gui, "No number",
                                     "'%s' is not a valid number" % self.gui.txtNodat.text())
                self.gui.txtNodat.setText("")
                return
        self.nodat = nodat
        self.gui.close()


# GUI specification for progressbar dialog
class PRG:
    def __init__(self, main):
        self.main = main
        self.gui = PRG_GUI()
        self.gui.lblCancel.setVisible(False)
        self.connections()

    def connections(self):
        self.gui.cmdCancel.clicked.connect(lambda: self.gui.close())

    def cancel(self):
        self.gui.allow_cancel = True
        self.gui.cmdCancel.setDisabled(True)
        self.gui.lblCancel.setText("-1")


# class MainUiFunc is the interface between all sub-GUIs, so they can communicate between each other
class MainUiFunc:
    def __init__(self):
        self.qgis_app = QApplication.instance()  # the QGIS-Application made accessible within the code
        self.vit = VIT(self)
        self.nodat_widget = Nodat(self)
        self.prg_widget = PRG(self)

    def show(self):
        self.vit.gui.show()


if __name__ == '__main__':
    from enmapbox.testing import start_app

    app = start_app()
    m = MainUiFunc()
    m.show()
    sys.exit(app.exec_())
