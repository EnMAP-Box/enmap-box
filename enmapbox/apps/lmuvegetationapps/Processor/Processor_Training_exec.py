# -*- coding: utf-8 -*-

import lmuvegetationapps.Processor.Processor_Inversion_core as processor

lut_path = r"E:\LUTs\MNI_LUT_D_5k_00meta.lut"

exclude_wavelengths = [[1290, 1525], [1730, 1970], [2450, 2500]]

wl = list(range(400, 2501))
exclude_bands = [i for i in range(len(wl)) if wl[i] < 400 or wl[i] > 2500
                 or exclude_wavelengths[0][0] <= wl[i] <= exclude_wavelengths[0][1]
                 or exclude_wavelengths[1][0] <= wl[i] <= exclude_wavelengths[1][1]
                 or exclude_wavelengths[2][0] <= wl[i] <= exclude_wavelengths[2][1]]

npca = 20
model_meta = r"E:\LUTs\MNI_LUT_D_5k.meta"

proc = processor.ProcessorMainFunction()  # instance of the Processor main class

# Setup everything for training
proc.train_main.training_setup(lut_metafile=lut_path, exclude_bands=exclude_bands, npca=npca,
                               model_meta=model_meta, algorithm='al_gpr_internal')

proc.train_main.validation_setup(val_file="E:\Testdaten\InSitu_LAI_spectra_EnMAP_noWaterV.txt",
                                 exclude_bands=exclude_bands, npca=npca)

proc.train_main.train_and_dump(prgbar_widget=None, qgis_app=None)
