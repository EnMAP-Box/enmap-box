# -*- coding: utf-8 -*-

"""
***************************************************************************
   algorithms.py

This is EnGeoMAP further information can be found in the following open acess publication:
Mielke, C.; Rogass, C.; Boesche, N.; Segl, K.; Altenberger, U. 
EnGeoMAP 2.0�Automated Hyperspectral Mineral Identification for the German EnMAP Space Mission. 
Remote Sens. 2016, 8, 127. 
    ---------------------
    Date                 : Juli 2019
    Copyright            : (C) 2019 by Christian Mielke
    Email                : christian.mielke@gfz-potsdam.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

Changelog
EnGeoMAP Version 3.2
Date: February 2023
Author: Helge L. C. Daempfling
Email: hdaemp@gfz-potsdam.de

The following modifications to the EnGeoMAP 3.1 release were realized:

- support for .esl and .sli file name extension as library input was added
(in prior versions manual removal of suffixes was necessary)

- data output names were changed for more clarity:

data type: correlat -> '_feature_fitting_correlation_scores'
-> '_feature_fitting_highest_correlation_result'

data type: bvlss -> '_bvls_unmixing_scores'
-> 'bvls_unmixing_highest_abundance_result'

"""
import os
from engeomap import engeomap_aux_funcul as auxfunul


def thresholder(guidat):
    try:
        guidat = guidat.strip()
        guidat = float(guidat)
    except(Exception):
        print("Threshold Exception: Please use float values between 0 and 1")
        return None
    if (guidat >= 0) and (guidat <= 1):
        pass
    else:
        print("Threshold Exception: Please use float values between 0 and 1")
        return None
    return guidat


def thresholder2(guidat):
    try:
        guidat = guidat.strip()
        guidat = int(guidat)
    except(Exception):
        print("Threshold Exception: Only int values greater 1 allowed")
        return None
    if (guidat > 1):
        pass
    else:
        print("Threshold Exception: Only int values greater 1 allowed")
        return None
    return guidat


def brp(path):
    if '.' in path:
        hdr = path.split('.')[0] + ".hdr"
    else:
        hdr = path.strip() + ".hdr"
    return path.strip(), hdr


def engeomapp_headless(params):
    # Parameter:
    print('EnGeoMAP: processing user input')
    print('VNIR threshold: '+params['vnirt'])
    print('SWIR threshold: '+params['swirt'])
    print('Minimum fit threshold: '+params['fit_thresh'])
    print('Max number of endmembers in unmixing: '+params['mixminerals'])
    # print(params['enmap'])
    # print(params['hyperion'])
    # print(params['laboratory'])
    # print(params['liblab'])
    print('Path to image data: '+params['image'])
    print('Path to spectral library: '+params['library'])
    print('Path to CSV color file: '+params['farbe'])
    vnirt = thresholder(params['vnirt'])
    swirt = thresholder(params['swirt'])
    fit_thr = thresholder(params['fit_thresh'])
    mix_minerals = thresholder2(params['mixminerals'])
    imasch = brp(params['image'])  # [0]==data [1]==header
    lib = brp(params['library'])
    farb = brp(params['farbe'])
    # sensor = sensorbuhl(params['enmap'])
    # liblab = float(params['liblab'])
    # lab = float(params['laboratory'])
    ###################################


# def mapper_fullrange(bildname,libname,colorfile):
def mapper_fullrange(params):
    # Var defs, params
    bildname = params['image']
    libname = (params['library'])
    colorfile = params['farbe']
    vnir_thr = thresholder(params['vnirt'])
    swir_thr = thresholder(params['swirt'])
    mix_minerals = thresholder2(params['mixminerals'])
    fit_threshold = thresholder(params['fit_thresh'])
    lib_flag = 0
    basename = bildname.split('.')[0]

    ###############################################

    # check and modify the .hdr file of the library for processing

    print(libname)
    tempTuple = os.path.splitext(libname)
    libnameh = tempTuple[0]
    print(libnameh)
    file = open(libnameh + ".hdr", "r")
    replacement = ""

    for line in file:
        line = line.strip()
        changes = line.replace("file type = ENVI Spectral Library", "file type = ENVI Standard")
        replacement = replacement + changes + "\n"

    file.close()

    fout = open(libnameh + ".hdr", "w")
    fout.write(replacement)
    fout.close()

    ###############################################

    # Load and check data:

    wbild, w1nmbild, bilddata = auxfunul.check_load_data(bildname)

    wlib, w1nmlib, libdata = auxfunul.check_load_data(libname)

    # Data Shape
    lsh = libdata.shape
    bsh = bilddata.shape

    # set flags min max
    minn, maxx, minflag, maxflag = auxfunul.compare_wavelengths(w1nmlib, w1nmbild)

    # interpolate
    interpol_wvls = auxfunul.prep_1nm_interpol_intersect(minn, maxx, minflag, maxflag, w1nmlib, w1nmbild)

    # Calculations Library:
    cvxabs_mod, cvxrel_mod, libdat_rel_weighted, libdat_rel_chm_weighted, vnirmax, swirmax = auxfunul.treat_library_cvx_full_range(
        wlib, libdata, interpol_wvls, vnir_thr, swir_thr)

    # Claculations Image:
    correlat, bvlss, bvlserr, vnirposmat, vnirdepthmat, swirposmat, swirdepthmat, astsum, depthsum, flsum, allessum = auxfunul.fitting_cvx_fullrange(
        wbild, interpol_wvls, bilddata, libdat_rel_weighted, libdat_rel_chm_weighted, cvxabs_mod, vnir_thr,
        swir_thr, lib_flag, mix_minerals, fit_threshold)

    # Schreib-Funktionen:

    auxfunul.reshreib(correlat, basename + '_feature_fitting_correlation_scores', [lsh[0], bsh[1], bsh[2]])
    auxfunul.reshreib(bvlss, basename + '_bvls_unmixing_scores', [lsh[0], bsh[1], bsh[2]])

    # Optional
    """
    auxfunul.reshreib2d(bvlserr, basename + '_abundance_residuals', [bsh[1], bsh[2]])
    """

    rgbdurchschn, indexmatdurchschn = auxfunul.corr_colours(correlat,
                                                            colorfile,
                                                            basename + '_feature_fitting_highest_correlation',
                                                            [lsh[0],
                                                             bsh[1],
                                                             bsh[2]],
                                                            minerals=lsh[
                                                                0])
    rgbu, indexmatu = auxfunul.corr_colours_unmix(bvlss, colorfile,
                                                  basename + '_bvls_unmixing',
                                                  [lsh[0], bsh[1], bsh[2]], minerals=lsh[0])

    """
    rgbdurchschn, indexmatdurchschn, rgbmdurchschn = auxfunul.corr_colours(correlat,
                                                                           colorfile,
                                                                           basename + '_feature_fitting_highest_correlation',
                                                                           [lsh[0],
                                                                            bsh[1],
                                                                            bsh[2]],
                                                                           minerals=lsh[
                                                                               0])
    rgbu, indexmatu, rgbum = auxfunul.corr_colours_unmix(bvlss, colorfile,
                                                         basename + '_abundance_unmix_',
                                                         [lsh[0], bsh[1], bsh[2]], minerals=lsh[0])
    """
    """
    # Additional data products
    auxfunul.reshreib2d(vnirposmat, basename + '_vnirpos_of_max_abs', [bsh[1], bsh[2]])
    auxfunul.reshreib2d(swirposmat, basename + '_swirpos_of_max_abs', [bsh[1], bsh[2]])
    auxfunul.reshreib2d(vnirdepthmat, basename + '_vnirdepth_of_max_abs', [bsh[1], bsh[2]])
    auxfunul.reshreib2d(swirdepthmat, basename + '_swirdepth_of_max_abs', [bsh[1], bsh[2]])
    auxfunul.reshreib2d(astsum, basename + '_cum_depth_div_by_width', [bsh[1], bsh[2]])
    auxfunul.reshreib2d(flsum, basename + '_cum_peak_area', [bsh[1], bsh[2]])
    auxfunul.reshreib2d(depthsum, basename + '_cum_depth', [bsh[1], bsh[2]])

    cont1 = numpy.sum(bilddata, axis=0) * numpy.reshape(depthsum, (bsh[1], bsh[2]))
    cont2 = numpy.sum(bilddata, axis=0) * numpy.reshape(flsum, (bsh[1], bsh[2]))

    auxfunul.schreibeBSQsingle(cont1, basename + '_albedo_ndepth_contrast')
    auxfunul.schreibeBSQsingle(cont2, basename + '_albedo_narea_contrast')
    """

    auxfunul.rewrite_headers(basename + '.hdr')

    ###############################################

    # restore Spectral Library .hdr

    file = open(libnameh + ".hdr", "r")
    replacement = ""

    for line in file:
        line = line.strip()
        changes = line.replace("file type = ENVI Standard", "file type = ENVI Spectral Library")
        replacement = replacement + changes + "\n"

    file.close()

    fout = open(libnameh + ".hdr", "w")
    fout.write(replacement)
    fout.close()

    ###############################################

    print('finished')

    return
